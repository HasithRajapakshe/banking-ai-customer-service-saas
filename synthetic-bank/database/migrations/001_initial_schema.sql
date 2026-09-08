-- ============================================================
-- Banking AI Customer Service SaaS
-- Migration: 001_initial_schema.sql
-- Purpose:
--   Initial production-grade multi-tenant banking schema
--   for the synthetic banking demonstration environment.
--
-- PostgreSQL 16 + pgvector
-- ============================================================

BEGIN;

-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================
-- MIGRATION METADATA
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_migration (
    version         VARCHAR(50) PRIMARY KEY,
    description     TEXT NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- TENANTS
-- ============================================================

CREATE TABLE tenant (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code         VARCHAR(50) NOT NULL UNIQUE,
    legal_name          VARCHAR(255) NOT NULL,
    display_name        VARCHAR(255) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
    default_currency    CHAR(3) NOT NULL DEFAULT 'LKR',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_tenant_status
        CHECK (status IN ('active', 'suspended', 'inactive')),

    CONSTRAINT chk_tenant_currency
        CHECK (default_currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_tenant_status
    ON tenant(status);


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE customer (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL,
    customer_number     VARCHAR(50) NOT NULL,

    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,

    email               VARCHAR(255),
    phone               VARCHAR(50),

    date_of_birth       DATE,

    national_id_hash    VARCHAR(255),

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_customer_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_customer_tenant_number
        UNIQUE (tenant_id, customer_number),

    CONSTRAINT chk_customer_status
        CHECK (status IN ('active', 'blocked', 'inactive'))
);

CREATE INDEX idx_customer_tenant
    ON customer(tenant_id);

CREATE INDEX idx_customer_email
    ON customer(tenant_id, email);

CREATE INDEX idx_customer_status
    ON customer(tenant_id, status);


-- ============================================================
-- ROLES
-- ============================================================

CREATE TABLE role (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID,

    role_code            VARCHAR(50) NOT NULL,
    role_name            VARCHAR(100) NOT NULL,
    description          TEXT,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_role_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_role_tenant_code
        UNIQUE (tenant_id, role_code)
);


-- ============================================================
-- PERMISSIONS
-- ============================================================

CREATE TABLE permission (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    permission_code     VARCHAR(100) NOT NULL UNIQUE,
    permission_name     VARCHAR(150) NOT NULL,
    description         TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- ROLE → PERMISSION
-- ============================================================

CREATE TABLE role_permission (
    role_id             UUID NOT NULL,
    permission_id       UUID NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (role_id, permission_id),

    CONSTRAINT fk_role_permission_role
        FOREIGN KEY (role_id)
        REFERENCES role(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_role_permission_permission
        FOREIGN KEY (permission_id)
        REFERENCES permission(id)
        ON DELETE CASCADE
);


-- ============================================================
-- APPLICATION USERS
-- ============================================================

CREATE TABLE app_user (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,

    customer_id         UUID,

    external_subject    VARCHAR(255),

    email               VARCHAR(255) NOT NULL,

    password_hash       VARCHAR(255),

    first_name          VARCHAR(100),
    last_name           VARCHAR(100),

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    last_login_at       TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_app_user_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_app_user_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_app_user_tenant_email
        UNIQUE (tenant_id, email),

    CONSTRAINT chk_app_user_status
        CHECK (status IN ('active', 'locked', 'disabled'))
);

CREATE INDEX idx_app_user_tenant
    ON app_user(tenant_id);

CREATE INDEX idx_app_user_customer
    ON app_user(customer_id);

CREATE INDEX idx_app_user_external_subject
    ON app_user(tenant_id, external_subject);


-- ============================================================
-- USER → ROLE
-- ============================================================

CREATE TABLE user_role (
    user_id             UUID NOT NULL,
    role_id             UUID NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, role_id),

    CONSTRAINT fk_user_role_user
        FOREIGN KEY (user_id)
        REFERENCES app_user(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_role_role
        FOREIGN KEY (role_id)
        REFERENCES role(id)
        ON DELETE CASCADE
);


-- ============================================================
-- ACCOUNTS
-- ============================================================

CREATE TABLE account (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    account_number      VARCHAR(50) NOT NULL,

    account_type        VARCHAR(30) NOT NULL,
    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    current_balance     NUMERIC(19,4) NOT NULL DEFAULT 0,
    available_balance   NUMERIC(19,4) NOT NULL DEFAULT 0,

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    opened_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at           TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_account_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_account_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_account_tenant_number
        UNIQUE (tenant_id, account_number),

    CONSTRAINT chk_account_type
        CHECK (
            account_type IN (
                'savings',
                'current',
                'salary',
                'fixed_deposit'
            )
        ),

    CONSTRAINT chk_account_status
        CHECK (
            status IN (
                'active',
                'blocked',
                'closed',
                'dormant'
            )
        ),

    CONSTRAINT chk_account_currency
        CHECK (currency ~ '^[A-Z]{3}$'),

    CONSTRAINT chk_account_balance
        CHECK (current_balance >= 0),

    CONSTRAINT chk_account_available_balance
        CHECK (available_balance >= 0)
);

CREATE INDEX idx_account_tenant
    ON account(tenant_id);

CREATE INDEX idx_account_customer
    ON account(tenant_id, customer_id);

CREATE INDEX idx_account_status
    ON account(tenant_id, status);


-- ============================================================
-- ACCOUNT TRANSACTIONS
-- ============================================================

CREATE TABLE account_transaction (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    account_id          UUID NOT NULL,

    transaction_number  VARCHAR(60) NOT NULL,

    transaction_type    VARCHAR(30) NOT NULL,

    amount              NUMERIC(19,4) NOT NULL,
    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    direction           VARCHAR(10) NOT NULL,

    balance_after       NUMERIC(19,4) NOT NULL,

    description         TEXT,

    merchant_name       VARCHAR(255),

    transaction_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_account_transaction_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_account_transaction_account
        FOREIGN KEY (account_id)
        REFERENCES account(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_account_transaction_number
        UNIQUE (tenant_id, transaction_number),

    CONSTRAINT chk_account_transaction_type
        CHECK (
            transaction_type IN (
                'purchase',
                'cash_withdrawal',
                'deposit',
                'transfer',
                'salary',
                'bill_payment',
                'fee',
                'refund',
                'interest',
                'other'
            )
        ),

    CONSTRAINT chk_account_transaction_direction
        CHECK (direction IN ('credit', 'debit')),

    CONSTRAINT chk_account_transaction_amount
        CHECK (amount > 0),

    CONSTRAINT chk_account_transaction_balance
        CHECK (balance_after >= 0),

    CONSTRAINT chk_account_transaction_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_account_transaction_account
    ON account_transaction(account_id, transaction_at DESC);

CREATE INDEX idx_account_transaction_tenant
    ON account_transaction(tenant_id, transaction_at DESC);


-- ============================================================
-- CARDS
-- ============================================================

CREATE TABLE card (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    card_number_hash    VARCHAR(255) NOT NULL,
    card_last4          CHAR(4) NOT NULL,

    card_type           VARCHAR(20) NOT NULL,

    expiry_month        SMALLINT NOT NULL,
    expiry_year         SMALLINT NOT NULL,

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    daily_limit         NUMERIC(19,4),

    issued_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    blocked_at          TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_card_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_card_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_card_number_hash
        UNIQUE (tenant_id, card_number_hash),

    CONSTRAINT chk_card_type
        CHECK (card_type IN ('debit', 'credit', 'prepaid')),

    CONSTRAINT chk_card_status
        CHECK (
            status IN (
                'active',
                'blocked',
                'expired',
                'cancelled'
            )
        ),

    CONSTRAINT chk_card_last4
        CHECK (card_last4 ~ '^[0-9]{4}$'),

    CONSTRAINT chk_card_expiry_month
        CHECK (expiry_month BETWEEN 1 AND 12),

    CONSTRAINT chk_card_daily_limit
        CHECK (daily_limit IS NULL OR daily_limit >= 0)
);

CREATE INDEX idx_card_customer
    ON card(tenant_id, customer_id);

CREATE INDEX idx_card_status
    ON card(tenant_id, status);


-- ============================================================
-- CARD TRANSACTIONS
-- ============================================================

CREATE TABLE card_transaction (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    card_id             UUID NOT NULL,

    transaction_number  VARCHAR(60) NOT NULL,

    amount              NUMERIC(19,4) NOT NULL,
    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    merchant_name       VARCHAR(255),
    merchant_category   VARCHAR(100),

    status              VARCHAR(20) NOT NULL DEFAULT 'completed',

    transaction_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_card_transaction_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_card_transaction_card
        FOREIGN KEY (card_id)
        REFERENCES card(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_card_transaction_number
        UNIQUE (tenant_id, transaction_number),

    CONSTRAINT chk_card_transaction_amount
        CHECK (amount > 0),

    CONSTRAINT chk_card_transaction_status
        CHECK (
            status IN (
                'pending',
                'completed',
                'reversed',
                'declined'
            )
        ),

    CONSTRAINT chk_card_transaction_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_card_transaction_card
    ON card_transaction(card_id, transaction_at DESC);

CREATE INDEX idx_card_transaction_tenant
    ON card_transaction(tenant_id, transaction_at DESC);


-- ============================================================
-- LOANS
-- ============================================================

CREATE TABLE loan (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    loan_number         VARCHAR(60) NOT NULL,

    loan_type           VARCHAR(30) NOT NULL,

    principal_amount    NUMERIC(19,4) NOT NULL,
    outstanding_amount  NUMERIC(19,4) NOT NULL,

    interest_rate       NUMERIC(8,4) NOT NULL,

    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    start_date          DATE NOT NULL,
    maturity_date       DATE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_loan_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_loan_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_loan_number
        UNIQUE (tenant_id, loan_number),

    CONSTRAINT chk_loan_type
        CHECK (
            loan_type IN (
                'personal',
                'home',
                'vehicle',
                'education',
                'business'
            )
        ),

    CONSTRAINT chk_loan_status
        CHECK (
            status IN (
                'active',
                'closed',
                'defaulted',
                'pending'
            )
        ),

    CONSTRAINT chk_loan_principal
        CHECK (principal_amount > 0),

    CONSTRAINT chk_loan_outstanding
        CHECK (outstanding_amount >= 0),

    CONSTRAINT chk_loan_interest_rate
        CHECK (interest_rate >= 0),

    CONSTRAINT chk_loan_currency
        CHECK (currency ~ '^[A-Z]{3}$'),

    CONSTRAINT chk_loan_dates
        CHECK (
            maturity_date IS NULL
            OR maturity_date >= start_date
        )
);

CREATE INDEX idx_loan_customer
    ON loan(tenant_id, customer_id);

CREATE INDEX idx_loan_status
    ON loan(tenant_id, status);


-- ============================================================
-- LOAN PAYMENTS
-- ============================================================

CREATE TABLE loan_payment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    loan_id             UUID NOT NULL,

    payment_number      VARCHAR(60) NOT NULL,

    installment_number  INTEGER NOT NULL,

    amount              NUMERIC(19,4) NOT NULL,

    principal_component NUMERIC(19,4) NOT NULL,
    interest_component  NUMERIC(19,4) NOT NULL,

    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    due_date            DATE NOT NULL,
    paid_at             TIMESTAMPTZ,

    status              VARCHAR(20) NOT NULL DEFAULT 'scheduled',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_loan_payment_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_loan_payment_loan
        FOREIGN KEY (loan_id)
        REFERENCES loan(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_loan_payment_number
        UNIQUE (tenant_id, payment_number),

    CONSTRAINT uq_loan_installment
        UNIQUE (loan_id, installment_number),

    CONSTRAINT chk_loan_payment_amount
        CHECK (amount > 0),

    CONSTRAINT chk_loan_payment_principal
        CHECK (principal_component >= 0),

    CONSTRAINT chk_loan_payment_interest
        CHECK (interest_component >= 0),

    CONSTRAINT chk_loan_payment_status
        CHECK (
            status IN (
                'scheduled',
                'paid',
                'overdue',
                'cancelled'
            )
        ),

    CONSTRAINT chk_loan_payment_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_loan_payment_loan
    ON loan_payment(loan_id, due_date);

CREATE INDEX idx_loan_payment_status
    ON loan_payment(tenant_id, status);


-- ============================================================
-- BENEFICIARIES
-- ============================================================

CREATE TABLE beneficiary (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    beneficiary_number  VARCHAR(60) NOT NULL,

    beneficiary_name    VARCHAR(255) NOT NULL,

    bank_name           VARCHAR(255),

    account_number_masked VARCHAR(100),

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_beneficiary_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_beneficiary_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_beneficiary_number
        UNIQUE (tenant_id, beneficiary_number),

    CONSTRAINT chk_beneficiary_status
        CHECK (
            status IN (
                'active',
                'blocked',
                'deleted'
            )
        )
);

CREATE INDEX idx_beneficiary_customer
    ON beneficiary(tenant_id, customer_id);


-- ============================================================
-- PAYMENTS
-- ============================================================

CREATE TABLE payment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    source_account_id   UUID NOT NULL,
    beneficiary_id      UUID NOT NULL,

    payment_number      VARCHAR(60) NOT NULL,

    amount              NUMERIC(19,4) NOT NULL,
    currency            CHAR(3) NOT NULL DEFAULT 'LKR',

    payment_reference   VARCHAR(255),

    status              VARCHAR(20) NOT NULL DEFAULT 'pending',

    idempotency_key     VARCHAR(255),

    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_payment_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_source_account
        FOREIGN KEY (source_account_id)
        REFERENCES account(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_beneficiary
        FOREIGN KEY (beneficiary_id)
        REFERENCES beneficiary(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_payment_number
        UNIQUE (tenant_id, payment_number),

    CONSTRAINT uq_payment_idempotency
        UNIQUE (tenant_id, idempotency_key),

    CONSTRAINT chk_payment_amount
        CHECK (amount > 0),

    CONSTRAINT chk_payment_status
        CHECK (
            status IN (
                'pending',
                'processing',
                'completed',
                'failed',
                'cancelled'
            )
        ),

    CONSTRAINT chk_payment_currency
        CHECK (currency ~ '^[A-Z]{3}$')
);

CREATE INDEX idx_payment_customer
    ON payment(tenant_id, customer_id, created_at DESC);

CREATE INDEX idx_payment_status
    ON payment(tenant_id, status);


-- ============================================================
-- COMPLAINTS
-- ============================================================

CREATE TABLE complaint (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID NOT NULL,

    complaint_number    VARCHAR(60) NOT NULL,

    category            VARCHAR(50) NOT NULL,

    priority            VARCHAR(20) NOT NULL DEFAULT 'medium',

    subject             VARCHAR(255) NOT NULL,
    description         TEXT NOT NULL,

    status              VARCHAR(30) NOT NULL DEFAULT 'open',

    assigned_to         UUID,

    resolved_at         TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_complaint_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_complaint_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_complaint_assignee
        FOREIGN KEY (assigned_to)
        REFERENCES app_user(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_complaint_number
        UNIQUE (tenant_id, complaint_number),

    CONSTRAINT chk_complaint_priority
        CHECK (
            priority IN (
                'low',
                'medium',
                'high',
                'critical'
            )
        ),

    CONSTRAINT chk_complaint_status
        CHECK (
            status IN (
                'open',
                'in_progress',
                'waiting_customer',
                'resolved',
                'closed'
            )
        )
);

CREATE INDEX idx_complaint_customer
    ON complaint(tenant_id, customer_id);

CREATE INDEX idx_complaint_status
    ON complaint(tenant_id, status);


-- ============================================================
-- SUPPORT TICKETS
-- ============================================================

CREATE TABLE support_ticket (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID,

    ticket_number       VARCHAR(60) NOT NULL,

    category            VARCHAR(50),
    priority            VARCHAR(20) NOT NULL DEFAULT 'medium',

    subject             VARCHAR(255) NOT NULL,
    description         TEXT,

    status              VARCHAR(30) NOT NULL DEFAULT 'open',

    assigned_to         UUID,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,

    CONSTRAINT fk_support_ticket_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_support_ticket_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_support_ticket_assignee
        FOREIGN KEY (assigned_to)
        REFERENCES app_user(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_support_ticket_number
        UNIQUE (tenant_id, ticket_number),

    CONSTRAINT chk_support_ticket_priority
        CHECK (
            priority IN (
                'low',
                'medium',
                'high',
                'critical'
            )
        ),

    CONSTRAINT chk_support_ticket_status
        CHECK (
            status IN (
                'open',
                'in_progress',
                'waiting_customer',
                'resolved',
                'closed'
            )
        )
);

CREATE INDEX idx_support_ticket_customer
    ON support_ticket(tenant_id, customer_id);

CREATE INDEX idx_support_ticket_status
    ON support_ticket(tenant_id, status);


-- ============================================================
-- CONVERSATIONS
-- ============================================================

CREATE TABLE conversation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    customer_id         UUID,

    conversation_number VARCHAR(60) NOT NULL,

    channel             VARCHAR(30) NOT NULL DEFAULT 'web',

    status              VARCHAR(20) NOT NULL DEFAULT 'active',

    title               VARCHAR(255),

    summary             TEXT,

    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_conversation_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_conversation_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_conversation_number
        UNIQUE (tenant_id, conversation_number),

    CONSTRAINT chk_conversation_channel
        CHECK (
            channel IN (
                'web',
                'mobile',
                'api',
                'whatsapp',
                'voice'
            )
        ),

    CONSTRAINT chk_conversation_status
        CHECK (
            status IN (
                'active',
                'closed',
                'escalated'
            )
        )
);

CREATE INDEX idx_conversation_customer
    ON conversation(tenant_id, customer_id, started_at DESC);

CREATE INDEX idx_conversation_status
    ON conversation(tenant_id, status);


-- ============================================================
-- MESSAGES
-- ============================================================

CREATE TABLE message (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    conversation_id     UUID NOT NULL,

    sender_type         VARCHAR(20) NOT NULL,

    content             TEXT NOT NULL,

    intent              VARCHAR(100),

    model_name          VARCHAR(100),

    token_count         INTEGER,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_message_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_message_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversation(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_message_sender
        CHECK (
            sender_type IN (
                'customer',
                'assistant',
                'system',
                'agent'
            )
        ),

    CONSTRAINT chk_message_token_count
        CHECK (
            token_count IS NULL
            OR token_count >= 0
        )
);

CREATE INDEX idx_message_conversation
    ON message(conversation_id, created_at);

CREATE INDEX idx_message_tenant
    ON message(tenant_id, created_at DESC);


-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID,

    actor_user_id       UUID,

    action              VARCHAR(100) NOT NULL,

    resource_type       VARCHAR(100),
    resource_id         UUID,

    correlation_id      VARCHAR(100),

    ip_address          INET,

    user_agent          TEXT,

    success             BOOLEAN NOT NULL DEFAULT TRUE,

    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_audit_actor
        FOREIGN KEY (actor_user_id)
        REFERENCES app_user(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_audit_tenant_time
    ON audit_log(tenant_id, created_at DESC);

CREATE INDEX idx_audit_actor
    ON audit_log(actor_user_id, created_at DESC);

CREATE INDEX idx_audit_correlation
    ON audit_log(correlation_id);

CREATE INDEX idx_audit_resource
    ON audit_log(resource_type, resource_id);


-- ============================================================
-- TOOL EXECUTIONS
-- ============================================================

CREATE TABLE tool_execution (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,

    user_id             UUID,

    conversation_id     UUID,

    tool_name           VARCHAR(100) NOT NULL,

    risk_level          VARCHAR(20) NOT NULL,

    status              VARCHAR(30) NOT NULL DEFAULT 'requested',

    authorization_result VARCHAR(30),

    idempotency_key     VARCHAR(255),

    request_payload     JSONB NOT NULL DEFAULT '{}'::jsonb,

    response_payload    JSONB,

    error_code          VARCHAR(100),

    error_message       TEXT,

    correlation_id      VARCHAR(100),

    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at        TIMESTAMPTZ,

    CONSTRAINT fk_tool_execution_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_tool_execution_user
        FOREIGN KEY (user_id)
        REFERENCES app_user(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_tool_execution_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversation(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_tool_execution_idempotency
        UNIQUE (tenant_id, idempotency_key),

    CONSTRAINT chk_tool_execution_risk
        CHECK (
            risk_level IN (
                'low',
                'medium',
                'high',
                'critical'
            )
        ),

    CONSTRAINT chk_tool_execution_status
        CHECK (
            status IN (
                'requested',
                'authorized',
                'denied',
                'executing',
                'succeeded',
                'failed',
                'timeout',
                'cancelled',
                'requires_approval'
            )
        )
);

CREATE INDEX idx_tool_execution_tenant
    ON tool_execution(tenant_id, requested_at DESC);

CREATE INDEX idx_tool_execution_conversation
    ON tool_execution(conversation_id);

CREATE INDEX idx_tool_execution_status
    ON tool_execution(tenant_id, status);


-- ============================================================
-- DOCUMENTS
-- ============================================================

CREATE TABLE document (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,

    document_key        VARCHAR(100) NOT NULL,

    title               VARCHAR(255) NOT NULL,

    document_type       VARCHAR(50) NOT NULL,

    status              VARCHAR(30) NOT NULL DEFAULT 'draft',

    owner_user_id       UUID,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_document_owner
        FOREIGN KEY (owner_user_id)
        REFERENCES app_user(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_document_key
        UNIQUE (tenant_id, document_key),

    CONSTRAINT chk_document_status
        CHECK (
            status IN (
                'draft',
                'in_review',
                'approved',
                'published',
                'archived'
            )
        )
);

CREATE INDEX idx_document_tenant
    ON document(tenant_id);

CREATE INDEX idx_document_status
    ON document(tenant_id, status);


-- ============================================================
-- DOCUMENT VERSIONS
-- ============================================================

CREATE TABLE document_version (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,
    document_id         UUID NOT NULL,

    version_number      INTEGER NOT NULL,

    content_hash        VARCHAR(128) NOT NULL,

    status              VARCHAR(30) NOT NULL DEFAULT 'draft',

    effective_from      TIMESTAMPTZ,
    effective_until     TIMESTAMPTZ,

    approved_by         UUID,
    approved_at         TIMESTAMPTZ,

    published_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_version_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_document_version_document
        FOREIGN KEY (document_id)
        REFERENCES document(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_document_version_approver
        FOREIGN KEY (approved_by)
        REFERENCES app_user(id)
        ON DELETE SET NULL,

    CONSTRAINT uq_document_version
        UNIQUE (document_id, version_number),

    CONSTRAINT chk_document_version_number
        CHECK (version_number > 0),

    CONSTRAINT chk_document_version_status
        CHECK (
            status IN (
                'draft',
                'in_review',
                'approved',
                'published',
                'superseded',
                'archived'
            )
        ),

    CONSTRAINT chk_document_version_dates
        CHECK (
            effective_until IS NULL
            OR effective_from IS NULL
            OR effective_until > effective_from
        )
);

CREATE INDEX idx_document_version_document
    ON document_version(document_id, version_number DESC);

CREATE INDEX idx_document_version_effective
    ON document_version(
        tenant_id,
        effective_from,
        effective_until
    );


-- ============================================================
-- DOCUMENT CHUNKS
-- ============================================================

CREATE TABLE document_chunk (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id           UUID NOT NULL,

    document_id         UUID NOT NULL,
    document_version_id UUID NOT NULL,

    chunk_index         INTEGER NOT NULL,

    content             TEXT NOT NULL,

    content_hash        VARCHAR(128) NOT NULL,

    token_count         INTEGER,

    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Initial embedding dimension.
    -- Can be changed through a future migration if the
    -- selected embedding provider/model uses another dimension.
    embedding           vector(1536),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_chunk_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_document_chunk_document
        FOREIGN KEY (document_id)
        REFERENCES document(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_document_chunk_version
        FOREIGN KEY (document_version_id)
        REFERENCES document_version(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_document_chunk_index
        UNIQUE (document_version_id, chunk_index),

    CONSTRAINT chk_document_chunk_index
        CHECK (chunk_index >= 0),

    CONSTRAINT chk_document_chunk_token_count
        CHECK (
            token_count IS NULL
            OR token_count >= 0
        )
);

CREATE INDEX idx_document_chunk_tenant
    ON document_chunk(tenant_id);

CREATE INDEX idx_document_chunk_version
    ON document_chunk(document_version_id);

CREATE INDEX idx_document_chunk_document
    ON document_chunk(document_id);


-- ============================================================
-- VECTOR INDEX
-- ============================================================

CREATE INDEX idx_document_chunk_embedding_hnsw
    ON document_chunk
    USING hnsw (embedding vector_cosine_ops);


-- ============================================================
-- JSONB INDEXES
-- ============================================================

CREATE INDEX idx_document_chunk_metadata
    ON document_chunk
    USING gin(metadata);

CREATE INDEX idx_audit_metadata
    ON audit_log
    USING gin(metadata);


-- ============================================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


-- ============================================================
-- UPDATED_AT TRIGGERS
-- ============================================================

CREATE TRIGGER trg_tenant_updated_at
BEFORE UPDATE ON tenant
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_customer_updated_at
BEFORE UPDATE ON customer
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_app_user_updated_at
BEFORE UPDATE ON app_user
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_account_updated_at
BEFORE UPDATE ON account
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_card_updated_at
BEFORE UPDATE ON card
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_loan_updated_at
BEFORE UPDATE ON loan
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_beneficiary_updated_at
BEFORE UPDATE ON beneficiary
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_payment_updated_at
BEFORE UPDATE ON payment
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_complaint_updated_at
BEFORE UPDATE ON complaint
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_support_ticket_updated_at
BEFORE UPDATE ON support_ticket
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_conversation_updated_at
BEFORE UPDATE ON conversation
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_document_updated_at
BEFORE UPDATE ON document
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- GLOBAL PERMISSIONS
-- ============================================================

INSERT INTO permission (
    permission_code,
    permission_name,
    description
)
VALUES
    ('chat.read', 'Read conversations', 'Read customer conversations'),
    ('chat.write', 'Send messages', 'Send customer service messages'),

    ('account.read', 'Read account information', 'View authorized account information'),
    ('transaction.read', 'Read transactions', 'View authorized account transactions'),

    ('card.read', 'Read card information', 'View authorized card information'),
    ('card.block', 'Block card', 'Block an authorized customer card'),

    ('loan.read', 'Read loan information', 'View authorized loan information'),

    ('payment.read', 'Read payments', 'View payment information'),
    ('payment.create', 'Create payment', 'Create an authorized payment'),

    ('complaint.create', 'Create complaint', 'Create a customer complaint'),
    ('complaint.read', 'Read complaint', 'Read complaint information'),

    ('ticket.create', 'Create support ticket', 'Create customer support ticket'),
    ('ticket.read', 'Read support ticket', 'Read support ticket'),

    ('knowledge.read', 'Read knowledge base', 'Retrieve approved knowledge'),
    ('knowledge.write', 'Manage knowledge base', 'Create and update knowledge'),
    ('knowledge.publish', 'Publish knowledge', 'Approve and publish knowledge'),

    ('analytics.read', 'Read analytics', 'View tenant analytics'),

    ('admin.users', 'Manage users', 'Manage tenant users'),
    ('admin.roles', 'Manage roles', 'Manage roles and permissions'),

    ('audit.read', 'Read audit logs', 'View security and activity audit logs')
ON CONFLICT (permission_code) DO NOTHING;


-- ============================================================
-- GLOBAL SYSTEM ROLES
-- tenant_id NULL = system/global role
-- ============================================================

INSERT INTO role (
    tenant_id,
    role_code,
    role_name,
    description
)
VALUES
    (
        NULL,
        'customer',
        'Customer',
        'Standard banking customer'
    ),
    (
        NULL,
        'support_agent',
        'Support Agent',
        'Human customer support agent'
    ),
    (
        NULL,
        'tenant_admin',
        'Tenant Administrator',
        'Administrator for a banking tenant'
    ),
    (
        NULL,
        'tenant_super_admin',
        'Tenant Super Administrator',
        'Full tenant administration privileges'
    )
ON CONFLICT DO NOTHING;


-- ============================================================
-- MIGRATION RECORD
-- ============================================================

INSERT INTO schema_migration (
    version,
    description
)
VALUES (
    '001',
    'Initial production-grade multi-tenant banking AI SaaS schema'
)
ON CONFLICT (version) DO NOTHING;


COMMIT;