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
