/**
 * Task Manager
 * Enforces task execution lifecycle, deduplication, and submission security approvals.
 */

import { ApplicationStatus, StructuredError } from '../shared/types/events';
import { SubmissionApproval } from '../shared/types/adapter';

export interface ActiveTaskState {
  task_id: string;
  workflow_id: string;
  operation: string;
  status: ApplicationStatus;
  progress: number;
  job_title?: string;
  company?: string;
  url?: string;
  started_at: string;
  approved_by_user: boolean;
  approval_token?: string;
}

export class TaskManager {
  private activeTask: ActiveTaskState | null = null;
  private completedTaskIds: Set<string> = new Set();
  private pendingApprovals: Map<string, SubmissionApproval> = new Map();

  public isTaskDuplicate(taskId: string): boolean {
    if (this.activeTask && this.activeTask.task_id === taskId) {
      return true;
    }
    return this.completedTaskIds.has(taskId);
  }

  public startTask(taskId: string, workflowId: string, operation: string, meta?: { job_title?: string; company?: string; url?: string }): ActiveTaskState {
    this.activeTask = {
      task_id: taskId,
      workflow_id: workflowId,
      operation,
      status: 'PREPARING',
      progress: 10,
      job_title: meta?.job_title,
      company: meta?.company,
      url: meta?.url,
      started_at: new Date().toISOString(),
      approved_by_user: false
    };
    return this.activeTask;
  }

  public updateTaskProgress(status: ApplicationStatus, progress: number, operation?: string): void {
    if (this.activeTask) {
      this.activeTask.status = status;
      this.activeTask.progress = progress;
      if (operation) this.activeTask.operation = operation;
    }
  }

  public recordApproval(applicationId: string, approvalToken: string): void {
    const approval: SubmissionApproval = {
      application_id: applicationId,
      workflow_id: this.activeTask?.workflow_id || 'wf-default',
      approved_by_user: true,
      approval_token: approvalToken,
      timestamp: new Date().toISOString()
    };
    this.pendingApprovals.set(applicationId, approval);
    if (this.activeTask) {
      this.activeTask.approved_by_user = true;
      this.activeTask.approval_token = approvalToken;
      this.activeTask.status = 'SUBMITTING';
    }
  }

  public verifyApproval(applicationId: string): SubmissionApproval | null {
    const approval = this.pendingApprovals.get(applicationId);
    if (!approval || !approval.approved_by_user) {
      return null;
    }
    return approval;
  }

  public completeTask(taskId: string): void {
    this.completedTaskIds.add(taskId);
    if (this.activeTask && this.activeTask.task_id === taskId) {
      this.activeTask.status = 'APPLIED';
      this.activeTask.progress = 100;
    }
  }

  public failTask(taskId: string, error: StructuredError): void {
    this.completedTaskIds.add(taskId);
    if (this.activeTask && this.activeTask.task_id === taskId) {
      this.activeTask.status = 'FAILED';
      this.activeTask.operation = `Error: ${error.message}`;
    }
  }

  public clearActiveTask(): void {
    this.activeTask = null;
  }

  public getActiveTask(): ActiveTaskState | null {
    return this.activeTask;
  }
}

export const taskManager = new TaskManager();

