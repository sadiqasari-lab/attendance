/**
 * Approvals service — approval requests CRUD + workflow actions.
 */
import type { ApprovalRequest, PaginatedResponse } from "@/types";
import api from "./api";

function tenantUrl(tenantSlug: string, path: string): string {
  return `/${tenantSlug}/approvals/approval-requests/${path}`;
}

export const approvalsService = {
  async getRequests(
    tenantSlug: string,
    params?: Record<string, string>
  ): Promise<PaginatedResponse<ApprovalRequest>> {
    const { data } = await api.get(tenantUrl(tenantSlug, ""), { params });
    return data;
  },

  async getRequest(tenantSlug: string, id: string): Promise<ApprovalRequest> {
    const { data } = await api.get(tenantUrl(tenantSlug, `${id}/`));
    return data;
  },

  async createRequest(
    tenantSlug: string,
    payload: {
      request_type: string;
      title: string;
      description: string;
      priority?: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<ApprovalRequest> {
    const { data } = await api.post(tenantUrl(tenantSlug, ""), payload);
    return data;
  },

  async approve(
    tenantSlug: string,
    id: string,
    review_notes?: string
  ): Promise<ApprovalRequest> {
    const { data } = await api.post(tenantUrl(tenantSlug, `${id}/approve/`), {
      review_notes: review_notes ?? "",
    });
    return data;
  },

  async reject(
    tenantSlug: string,
    id: string,
    review_notes?: string
  ): Promise<ApprovalRequest> {
    const { data } = await api.post(tenantUrl(tenantSlug, `${id}/reject/`), {
      review_notes: review_notes ?? "",
    });
    return data;
  },

  async cancel(tenantSlug: string, id: string): Promise<ApprovalRequest> {
    const { data } = await api.post(tenantUrl(tenantSlug, `${id}/cancel/`));
    return data;
  },

  async getPendingCount(tenantSlug: string): Promise<{ pending_count: number }> {
    const { data } = await api.get(tenantUrl(tenantSlug, "pending-count/"));
    return data;
  },
};
