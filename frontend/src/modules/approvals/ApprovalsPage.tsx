import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { DataTable } from "@/components/common/DataTable";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { approvalsService } from "@/services/approvals.service";
import { useAuthStore } from "@/store/authStore";
import type {
  ApprovalRequest,
  ApprovalStatus,
  ApprovalPriority,
  ApprovalRequestType,
} from "@/types";
import {
  CheckCircleIcon,
  XCircleIcon,
  XMarkIcon,
  EyeIcon,
  PlusIcon,
  FunnelIcon,
} from "@heroicons/react/24/outline";

// ---------- Status & Priority badge helpers ----------

const statusColors: Record<ApprovalStatus, string> = {
  PENDING: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  APPROVED: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  REJECTED: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  CANCELLED: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

const priorityColors: Record<ApprovalPriority, string> = {
  LOW: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  MEDIUM: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  HIGH: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  URGENT: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

export function ApprovalsPage() {
  const { t } = useTranslation();
  const { tenantSlug } = useParams<{ tenantSlug: string }>();
  const { user } = useAuthStore();

  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);

  // Detail / Create modal
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");

  // Create form
  const [createForm, setCreateForm] = useState({
    request_type: "ATTENDANCE_CORRECTION" as ApprovalRequestType,
    title: "",
    description: "",
    priority: "MEDIUM" as ApprovalPriority,
  });

  const isManager = user && ["SUPER_ADMIN", "TENANT_ADMIN", "MANAGER"].includes(user.role);

  // ---------- Fetch ----------
  const fetchRequests = useCallback(async () => {
    if (!tenantSlug) return;
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (typeFilter) params.request_type = typeFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await approvalsService.getRequests(tenantSlug, params);
      setRequests(res.results ?? []);
    } catch {
      // handled silently
    } finally {
      setLoading(false);
    }
  }, [tenantSlug, statusFilter, typeFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  // ---------- Actions ----------
  const handleApprove = async (id: string) => {
    if (!tenantSlug) return;
    setActionLoading(id);
    try {
      await approvalsService.approve(tenantSlug, id, reviewNotes);
      setReviewNotes("");
      setSelectedRequest(null);
      await fetchRequests();
    } catch {
      // handled silently
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: string) => {
    if (!tenantSlug) return;
    setActionLoading(id);
    try {
      await approvalsService.reject(tenantSlug, id, reviewNotes);
      setReviewNotes("");
      setSelectedRequest(null);
      await fetchRequests();
    } catch {
      // handled silently
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async (id: string) => {
    if (!tenantSlug) return;
    setActionLoading(id);
    try {
      await approvalsService.cancel(tenantSlug, id);
      setSelectedRequest(null);
      await fetchRequests();
    } catch {
      // handled silently
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreate = async () => {
    if (!tenantSlug) return;
    setActionLoading("create");
    try {
      await approvalsService.createRequest(tenantSlug, createForm);
      setShowCreateModal(false);
      setCreateForm({
        request_type: "ATTENDANCE_CORRECTION",
        title: "",
        description: "",
        priority: "MEDIUM",
      });
      await fetchRequests();
    } catch {
      // handled silently
    } finally {
      setActionLoading(null);
    }
  };

  // ---------- Table columns ----------
  const columns = [
    {
      key: "title",
      header: t("approvals.title_col"),
      render: (r: ApprovalRequest) => (
        <span className="font-medium text-gray-900 dark:text-white">{r.title}</span>
      ),
    },
    {
      key: "requester_name",
      header: t("approvals.requester"),
    },
    {
      key: "request_type_display",
      header: t("approvals.type"),
    },
    {
      key: "priority",
      header: t("approvals.priority"),
      render: (r: ApprovalRequest) => (
        <span className={`badge ${priorityColors[r.priority]}`}>
          {r.priority_display}
        </span>
      ),
    },
    {
      key: "status",
      header: t("approvals.status"),
      render: (r: ApprovalRequest) => (
        <span className={`badge ${statusColors[r.status]}`}>
          {r.status_display}
        </span>
      ),
    },
    {
      key: "created_at",
      header: t("approvals.created"),
      render: (r: ApprovalRequest) => new Date(r.created_at).toLocaleDateString(),
    },
    {
      key: "actions",
      header: t("common.actions"),
      render: (r: ApprovalRequest) => (
        <div className="flex items-center gap-1">
          <button
            onClick={() => { setSelectedRequest(r); setReviewNotes(""); }}
            className="rounded p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            title={t("approvals.view_details")}
          >
            <EyeIcon className="h-4 w-4" />
          </button>
          {isManager && r.status === "PENDING" && (
            <>
              <button
                onClick={() => handleApprove(r.id)}
                disabled={actionLoading === r.id}
                className="rounded p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20"
                title={t("approvals.approve")}
              >
                <CheckCircleIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => handleReject(r.id)}
                disabled={actionLoading === r.id}
                className="rounded p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                title={t("approvals.reject")}
              >
                <XCircleIcon className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t("approvals.page_title")}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary flex items-center gap-1"
          >
            <FunnelIcon className="h-4 w-4" />
            {t("approvals.filters")}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-1"
          >
            <PlusIcon className="h-4 w-4" />
            {t("approvals.new_request")}
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="card p-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t("approvals.filter_status")}
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input w-full"
              >
                <option value="">{t("approvals.all")}</option>
                <option value="PENDING">{t("approvals.status_pending")}</option>
                <option value="APPROVED">{t("approvals.status_approved")}</option>
                <option value="REJECTED">{t("approvals.status_rejected")}</option>
                <option value="CANCELLED">{t("approvals.status_cancelled")}</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t("approvals.filter_type")}
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="input w-full"
              >
                <option value="">{t("approvals.all")}</option>
                <option value="ATTENDANCE_CORRECTION">{t("approvals.type_attendance")}</option>
                <option value="DEVICE_CHANGE">{t("approvals.type_device")}</option>
                <option value="LEAVE_REQUEST">{t("approvals.type_leave")}</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t("approvals.filter_priority")}
              </label>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="input w-full"
              >
                <option value="">{t("approvals.all")}</option>
                <option value="LOW">{t("approvals.priority_low")}</option>
                <option value="MEDIUM">{t("approvals.priority_medium")}</option>
                <option value="HIGH">{t("approvals.priority_high")}</option>
                <option value="URGENT">{t("approvals.priority_urgent")}</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                {t("common.search")}
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("approvals.search_placeholder")}
                className="input w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <LoadingSpinner className="py-12" />
        ) : (
          <DataTable
            columns={columns}
            data={requests}
            keyExtractor={(r) => r.id}
            emptyMessage={t("approvals.no_requests")}
          />
        )}
      </div>

      {/* -------- Detail Modal -------- */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {selectedRequest.title}
              </h3>
              <button
                onClick={() => setSelectedRequest(null)}
                className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.requester")}</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {selectedRequest.requester_name} ({selectedRequest.requester_employee_id})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.type")}</span>
                <span>{selectedRequest.request_type_display}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.priority")}</span>
                <span className={`badge ${priorityColors[selectedRequest.priority]}`}>
                  {selectedRequest.priority_display}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.status")}</span>
                <span className={`badge ${statusColors[selectedRequest.status]}`}>
                  {selectedRequest.status_display}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.created")}</span>
                <span>{new Date(selectedRequest.created_at).toLocaleString()}</span>
              </div>

              <div>
                <span className="text-gray-500 dark:text-gray-400">{t("approvals.description")}</span>
                <p className="mt-1 rounded bg-gray-50 p-3 text-gray-700 dark:bg-gray-900 dark:text-gray-300">
                  {selectedRequest.description}
                </p>
              </div>

              {selectedRequest.reviewer_name && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">{t("approvals.reviewed_by")}</span>
                  <span>{selectedRequest.reviewer_name}</span>
                </div>
              )}

              {selectedRequest.review_notes && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">{t("approvals.review_notes")}</span>
                  <p className="mt-1 rounded bg-gray-50 p-3 text-gray-700 dark:bg-gray-900 dark:text-gray-300">
                    {selectedRequest.review_notes}
                  </p>
                </div>
              )}

              {/* Approve / Reject actions for managers on PENDING requests */}
              {isManager && selectedRequest.status === "PENDING" && (
                <div className="space-y-3 border-t border-gray-200 pt-4 dark:border-gray-700">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
                      {t("approvals.review_notes")}
                    </label>
                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      rows={2}
                      className="input w-full"
                      placeholder={t("approvals.review_notes_placeholder")}
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(selectedRequest.id)}
                      disabled={actionLoading === selectedRequest.id}
                      className="btn-primary flex-1 bg-green-600 hover:bg-green-700"
                    >
                      {actionLoading === selectedRequest.id
                        ? t("common.loading")
                        : t("approvals.approve")}
                    </button>
                    <button
                      onClick={() => handleReject(selectedRequest.id)}
                      disabled={actionLoading === selectedRequest.id}
                      className="btn-primary flex-1 bg-red-600 hover:bg-red-700"
                    >
                      {actionLoading === selectedRequest.id
                        ? t("common.loading")
                        : t("approvals.reject")}
                    </button>
                  </div>
                </div>
              )}

              {/* Cancel action for request owner */}
              {selectedRequest.status === "PENDING" && (
                <div className="border-t border-gray-200 pt-4 dark:border-gray-700">
                  <button
                    onClick={() => handleCancel(selectedRequest.id)}
                    disabled={actionLoading === selectedRequest.id}
                    className="btn-secondary w-full text-red-600"
                  >
                    {actionLoading === selectedRequest.id
                      ? t("common.loading")
                      : t("approvals.cancel_request")}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* -------- Create Modal -------- */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {t("approvals.new_request")}
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("approvals.type")}
                </label>
                <select
                  value={createForm.request_type}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, request_type: e.target.value as ApprovalRequestType })
                  }
                  className="input w-full"
                >
                  <option value="ATTENDANCE_CORRECTION">{t("approvals.type_attendance")}</option>
                  <option value="DEVICE_CHANGE">{t("approvals.type_device")}</option>
                  <option value="LEAVE_REQUEST">{t("approvals.type_leave")}</option>
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("approvals.title_col")}
                </label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="input w-full"
                  placeholder={t("approvals.title_placeholder")}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("approvals.description")}
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  rows={3}
                  className="input w-full"
                  placeholder={t("approvals.description_placeholder")}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("approvals.priority")}
                </label>
                <select
                  value={createForm.priority}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, priority: e.target.value as ApprovalPriority })
                  }
                  className="input w-full"
                >
                  <option value="LOW">{t("approvals.priority_low")}</option>
                  <option value="MEDIUM">{t("approvals.priority_medium")}</option>
                  <option value="HIGH">{t("approvals.priority_high")}</option>
                  <option value="URGENT">{t("approvals.priority_urgent")}</option>
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  {t("common.cancel")}
                </button>
                <button
                  onClick={handleCreate}
                  disabled={
                    actionLoading === "create" || !createForm.title || !createForm.description
                  }
                  className="btn-primary flex-1"
                >
                  {actionLoading === "create"
                    ? t("common.loading")
                    : t("approvals.submit_request")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
