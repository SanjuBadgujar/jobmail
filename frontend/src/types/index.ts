export interface DashboardStats {
  totalRecipients: number; sent: number; pending: number; failed: number; gmailConnected: boolean; gmailEmail?: string;
}
export const emptyStats: DashboardStats = { totalRecipients: 0, sent: 0, pending: 0, failed: 0, gmailConnected: false };
export interface Recipient { id: number; name: string | null; email: string; company: string | null; position: string | null }
export interface ResumeInfo { id: number; filename: string; fileSize: number }
export interface AuthStatus { authenticated: boolean; gmailConnected: boolean; email: string | null }
export interface QueueCampaign { id: number; subject: string; status: string; note: string | null; total: number; sent: number; failed: number; cancelled: number; pending: number; delaySeconds: number }
export interface HistoryRow { id: number; recipient: string; subject: string; time: string; status: string; error: string | null; gmailMessageId: string | null }
