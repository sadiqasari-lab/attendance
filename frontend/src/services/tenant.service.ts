/**
 * Tenant service — tenants, departments, employees.
 */
import type { Department, Employee, PaginatedResponse, Tenant } from "@/types";
import api from "./api";

export const tenantService = {
  async getTenants(): Promise<PaginatedResponse<Tenant>> {
    const { data } = await api.get("/tenants/");
    return data;
  },
  async getTenant(id: string): Promise<Tenant> {
    const { data } = await api.get(`/tenants/${id}/`);
    return data.data ?? data;
  },

  async getDepartments(tenantSlug: string): Promise<PaginatedResponse<Department>> {
    const { data } = await api.get(`/tenants/departments/?tenant_slug=${tenantSlug}`);
    return data;
  },

  async getEmployees(
    tenantSlug: string,
    params?: Record<string, string>
  ): Promise<PaginatedResponse<Employee>> {
    const { data } = await api.get(`/${tenantSlug}/attendance/records/`, {
      params: { ...params, _type: "employees" },
    });
    return data;
  },
};
