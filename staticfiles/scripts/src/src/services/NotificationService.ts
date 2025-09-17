export interface INotificationData {
  open: boolean;
  title: string;
  message: string;
  success: boolean;
  duration?: number;
}

export interface IConfirmDialogData {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export interface IToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export class NotificationService {
  private notifications: INotificationData[] = [];
  private confirmDialogs: IConfirmDialogData[] = [];
  private toastNotifications: IToastNotification[] = [];
  private listeners: Array<() => void> = [];

  /**
   * Show success notification
   */
  showSuccess(title: string, message: string, duration: number = 5000): void {
    this.showNotification({
      open: true,
      title,
      message,
      success: true,
      duration
    });
  }

  /**
   * Show error notification
   */
  showError(title: string, message: string, duration: number = 7000): void {
    this.showNotification({
      open: true,
      title,
      message,
      success: false,
      duration
    });
  }

  /**
   * Show warning notification
   */
  showWarning(title: string, message: string, duration: number = 6000): void {
    this.showToast({
      id: this.generateId(),
      type: 'warning',
      title,
      message,
      duration
    });
  }

  /**
   * Show info notification
   */
  showInfo(title: string, message: string, duration: number = 5000): void {
    this.showToast({
      id: this.generateId(),
      type: 'info',
      title,
      message,
      duration
    });
  }

  /**
   * Show main notification
   */
  showNotification(notification: INotificationData): void {
    this.notifications.push(notification);
    this.notifyListeners();

    // Auto-close after duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        this.closeNotification(notification);
      }, notification.duration);
    }
  }

  /**
   * Close notification
   */
  closeNotification(notification: INotificationData): void {
    const index = this.notifications.indexOf(notification);
    if (index > -1) {
      this.notifications.splice(index, 1);
      this.notifyListeners();
    }
  }

  /**
   * Close all notifications
   */
  closeAllNotifications(): void {
    this.notifications = [];
    this.notifyListeners();
  }

  /**
   * Show toast notification
   */
  showToast(toast: IToastNotification): void {
    this.toastNotifications.push(toast);
    this.notifyListeners();

    // Auto-remove after duration
    if (toast.duration && toast.duration > 0) {
      setTimeout(() => {
        this.removeToast(toast.id);
      }, toast.duration);
    }
  }

  /**
   * Remove toast notification
   */
  removeToast(id: string): void {
    const index = this.toastNotifications.findIndex(toast => toast.id === id);
    if (index > -1) {
      this.toastNotifications.splice(index, 1);
      this.notifyListeners();
    }
  }

  /**
   * Remove all toast notifications
   */
  removeAllToasts(): void {
    this.toastNotifications = [];
    this.notifyListeners();
  }

  /**
   * Show confirmation dialog
   */
  showConfirm(dialog: Omit<IConfirmDialogData, 'open'>): Promise<boolean> {
    return new Promise((resolve) => {
      const confirmDialog: IConfirmDialogData = {
        ...dialog,
        open: true,
        onConfirm: () => {
          this.closeConfirmDialog(confirmDialog);
          resolve(true);
        },
        onCancel: () => {
          this.closeConfirmDialog(confirmDialog);
          resolve(false);
        }
      };

      this.confirmDialogs.push(confirmDialog);
      this.notifyListeners();
    });
  }

  /**
   * Close confirmation dialog
   */
  closeConfirmDialog(dialog: IConfirmDialogData): void {
    const index = this.confirmDialogs.indexOf(dialog);
    if (index > -1) {
      this.confirmDialogs.splice(index, 1);
      this.notifyListeners();
    }
  }

  /**
   * Close all confirmation dialogs
   */
  closeAllConfirmDialogs(): void {
    this.confirmDialogs = [];
    this.notifyListeners();
  }

  /**
   * Show simple confirmation (using browser confirm)
   */
  confirm(message: string): Promise<boolean> {
    return Promise.resolve(window.confirm(message));
  }

  /**
   * Show simple alert (using browser alert)
   */
  alert(message: string): void {
    window.alert(message);
  }

  /**
   * Show success toast
   */
  successToast(title: string, message: string, duration?: number): void {
    this.showToast({
      id: this.generateId(),
      type: 'success',
      title,
      message,
      duration
    });
  }

  /**
   * Show error toast
   */
  errorToast(title: string, message: string, duration?: number): void {
    this.showToast({
      id: this.generateId(),
      type: 'error',
      title,
      message,
      duration
    });
  }

  /**
   * Show warning toast
   */
  warningToast(title: string, message: string, duration?: number): void {
    this.showToast({
      id: this.generateId(),
      type: 'warning',
      title,
      message,
      duration
    });
  }

  /**
   * Show info toast
   */
  infoToast(title: string, message: string, duration?: number): void {
    this.showToast({
      id: this.generateId(),
      type: 'info',
      title,
      message,
      duration
    });
  }

  /**
   * Show notification with action button
   */
  showNotificationWithAction(
    title: string,
    message: string,
    actionLabel: string,
    onAction: () => void,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    duration?: number
  ): void {
    this.showToast({
      id: this.generateId(),
      type,
      title,
      message,
      duration,
      action: {
        label: actionLabel,
        onClick: onAction
      }
    });
  }

  /**
   * Get current notifications
   */
  getNotifications(): INotificationData[] {
    return [...this.notifications];
  }

  /**
   * Get current confirmation dialogs
   */
  getConfirmDialogs(): IConfirmDialogData[] {
    return [...this.confirmDialogs];
  }

  /**
   * Get current toast notifications
   */
  getToastNotifications(): IToastNotification[] {
    return [...this.toastNotifications];
  }

  /**
   * Subscribe to notification changes
   */
  subscribe(listener: () => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify all listeners
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener());
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Show loading notification
   */
  showLoading(title: string, message: string): string {
    const loadingId = this.generateId();
    
    this.showToast({
      id: loadingId,
      type: 'info',
      title,
      message,
      duration: 0 // No auto-close
    });

    return loadingId;
  }

  /**
   * Hide loading notification
   */
  hideLoading(loadingId: string): void {
    this.removeToast(loadingId);
  }

  /**
   * Show progress notification
   */
  showProgress(title: string, message: string, progress: number): string {
    const progressId = this.generateId();
    
    this.showToast({
      id: progressId,
      type: 'info',
      title: `${title} (${Math.round(progress)}%)`,
      message,
      duration: 0 // No auto-close
    });

    return progressId;
  }

  /**
   * Update progress notification
   */
  updateProgress(progressId: string, title: string, message: string, progress: number): void {
    const toast = this.toastNotifications.find(t => t.id === progressId);
    if (toast) {
      toast.title = `${title} (${Math.round(progress)}%)`;
      toast.message = message;
      this.notifyListeners();
    }
  }

  /**
   * Complete progress notification
   */
  completeProgress(progressId: string, title: string, message: string, success: boolean = true): void {
    const toast = this.toastNotifications.find(t => t.id === progressId);
    if (toast) {
      toast.type = success ? 'success' : 'error';
      toast.title = title;
      toast.message = message;
      toast.duration = 5000; // Auto-close after 5 seconds
      this.notifyListeners();
    }
  }

  /**
   * Show network error notification
   */
  showNetworkError(): void {
    this.showError(
      "Network Error",
      "Unable to connect to the server. Please check your internet connection and try again.",
      10000
    );
  }

  /**
   * Show validation error notification
   */
  showValidationError(errors: string[]): void {
    if (errors.length === 1) {
      this.showError("Validation Error", errors[0]);
    } else {
      this.showError("Validation Errors", errors.join('\n'));
    }
  }

  /**
   * Show permission denied notification
   */
  showPermissionDenied(action: string): void {
    this.showError(
      "Access Denied",
      `You don't have permission to ${action}. Please contact your administrator.`
    );
  }

  /**
   * Show session expired notification
   */
  showSessionExpired(): void {
    this.showError(
      "Session Expired",
      "Your session has expired. Please log in again to continue.",
      0 // No auto-close
    );
  }
}
