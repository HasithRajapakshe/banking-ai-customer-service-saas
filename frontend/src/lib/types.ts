// Response shapes returned by the API Gateway.

// GET /api/v1/auth/me (api-gateway UserResponse)
export interface CurrentUser {
  id: string;
  tenant_id: string;
  customer_id: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// GET /api/v1/cards (banking-adapter card DTO)
export interface Card {
  id: string;
  card_type: string;
  card_last4: string;
  status: string;
}

// GET /api/v1/admin/audit
export interface AuditEntry {
  id: string;
  created_at: string;
  action: string;
  success: boolean;
  actor_user_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  correlation_id: string | null;
  metadata: Record<string, unknown>;
}

export interface AuditPage {
  items: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
}

// GET /api/v1/accounts (banking-adapter account DTO)
export interface Account {
  id: string;
  account_number: string;
  account_type: string;
  currency: string;
  current_balance: string;
  available_balance?: string;
  status?: string;
}
