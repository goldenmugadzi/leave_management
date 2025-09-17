/**
 * Consolidated Notification and Response Service
 * Handles all notifications, responses, and user feedback consistently across the application
 */

export interface INotificationData {
  id?: string;
  open: boolean;
  title: string;
  message: string;
  success?: boolean;
  warning?: boolean;
  error?: boolean;
  info?: boolean;
  duration?: number;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'danger' | 'success';
  }>;
  onClose?: () => void;
}

export interface IConfirmDialogData {
  id?: string;
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: 'primary' | 'secondary' | 'danger' | 'success';
  onConfirm: () => void;
  onCancel?: () => void;
  onClose?: () => void;
}

export interface IToastNotification {
  id?: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

export interface IResponseData {
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
  warnings?: string[];
  metadata?: {
    timestamp: string;
    requestId?: string;
    processingTime?: number;
  };
}

export interface IApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  statusCode?: number;
  timestamp: string;
}

export class NotificationResponseService {
  private static instance: NotificationResponseService;
  private notifications: INotificationData[] = [];
  private confirmDialogs: IConfirmDialogData[] = [];
  private toastNotifications: IToastNotification[] = [];
  private listeners: Array<() => void> = [];
  private responseHandlers: Map<string, (response: IResponseData) => void> = new Map();

  private constructor() {}

  /**
   * Get singleton instance
   */
  static getInstance(): NotificationResponseService {
    if (!NotificationResponseService.instance) {
      NotificationResponseService.instance = new NotificationResponseService();
    }
    return NotificationResponseService.instance;
  }

  // === NOTIFICATION METHODS ===

  /**
   * Show success notification
   */
  showSuccess(title: string, message: string, duration: number = 5000, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      success: true,
      duration,
      actions
    });
  }

  /**
   * Show error notification
   */
  showError(title: string, message: string, duration: number = 7000, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      error: true,
      duration,
      actions
    });
  }

  /**
   * Show warning notification
   */
  showWarning(title: string, message: string, duration: number = 6000, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      warning: true,
      duration,
      actions
    });
  }

  /**
   * Show info notification
   */
  showInfo(title: string, message: string, duration: number = 5000, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      info: true,
      duration,
      actions
    });
  }

  /**
   * Show main notification
   */
  showNotification(notification: INotificationData): void {
    const id = notification.id || this.generateId();
    const notificationWithId = { ...notification, id };
    
    this.notifications.push(notificationWithId);
    this.notifyListeners();

    // Auto-close after duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        this.closeNotification(notificationWithId);
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
   * Get all notifications
   */
  getNotifications(): INotificationData[] {
    return [...this.notifications];
  }

  // === CONFIRM DIALOG METHODS ===

  /**
   * Show confirm dialog
   */
  showConfirmDialog(dialog: IConfirmDialogData): void {
    const id = dialog.id || this.generateId();
    const dialogWithId = { 
      ...dialog, 
      id,
      confirmLabel: dialog.confirmLabel || 'Confirm',
      cancelLabel: dialog.cancelLabel || 'Cancel',
      confirmVariant: dialog.confirmVariant || 'primary'
    };
    
    this.confirmDialogs.push(dialogWithId);
    this.notifyListeners();
  }

  /**
   * Close confirm dialog
   */
  closeConfirmDialog(dialog: IConfirmDialogData): void {
    const index = this.confirmDialogs.indexOf(dialog);
    if (index > -1) {
      this.confirmDialogs.splice(index, 1);
      this.notifyListeners();
    }
  }

  /**
   * Get all confirm dialogs
   */
  getConfirmDialogs(): IConfirmDialogData[] {
    return [...this.confirmDialogs];
  }

  // === TOAST NOTIFICATION METHODS ===

  /**
   * Show toast notification
   */
  showToast(toast: IToastNotification): void {
    const id = toast.id || this.generateId();
    const toastWithId = { 
      ...toast, 
      id,
      duration: toast.duration || 4000,
      position: toast.position || 'top-right'
    };
    
    this.toastNotifications.push(toastWithId);
    this.notifyListeners();

    // Auto-remove after duration
    setTimeout(() => {
      this.removeToast(toastWithId);
    }, toastWithId.duration);
  }

  /**
   * Show success toast
   */
  showSuccessToast(message: string, title?: string, duration?: number): void {
    this.showToast({
      title: title || 'Success',
      message,
      type: 'success',
      duration
    });
  }

  /**
   * Show error toast
   */
  showErrorToast(message: string, title?: string, duration?: number): void {
    this.showToast({
      title: title || 'Error',
      message,
      type: 'error',
      duration
    });
  }

  /**
   * Show warning toast
   */
  showWarningToast(message: string, title?: string, duration?: number): void {
    this.showToast({
      title: title || 'Warning',
      message,
      type: 'warning',
      duration
    });
  }

  /**
   * Show info toast
   */
  showInfoToast(message: string, title?: string, duration?: number): void {
    this.showToast({
      title: title || 'Info',
      message,
      type: 'info',
      duration
    });
  }

  /**
   * Remove toast notification
   */
  removeToast(toast: IToastNotification): void {
    const index = this.toastNotifications.indexOf(toast);
    if (index > -1) {
      this.toastNotifications.splice(index, 1);
      this.notifyListeners();
    }
  }

  /**
   * Get all toast notifications
   */
  getToastNotifications(): IToastNotification[] {
    return [...this.toastNotifications];
  }

  // === RESPONSE HANDLING METHODS ===

  /**
   * Handle API response consistently
   */
  handleApiResponse<T>(response: IApiResponse<T>, context?: string): IResponseData {
    const responseData: IResponseData = {
      success: response.success,
      message: response.message,
      error: response.error,
      data: response.data,
      metadata: {
        timestamp: response.timestamp,
        requestId: this.generateId(),
        processingTime: Date.now() - new Date(response.timestamp).getTime()
      }
    };

    if (response.success) {
      if (response.message) {
        this.showSuccessToast(response.message, context);
      }
    } else {
      if (response.error) {
        this.showErrorToast(response.error, context || 'Request Failed');
      } else if (response.message) {
        this.showWarningToast(response.message, context);
      }
    }

    return responseData;
  }

  /**
   * Handle success response
   */
  handleSuccess(message: string, data?: any, context?: string): IResponseData {
    const responseData: IResponseData = {
      success: true,
      message,
      data,
      metadata: {
        timestamp: new Date().toISOString(),
        requestId: this.generateId()
      }
    };

    this.showSuccessToast(message, context);
    return responseData;
  }

  /**
   * Handle error response
   */
  handleError(error: string | Error, context?: string, data?: any): IResponseData {
    const errorMessage = error instanceof Error ? error.message : error;
    
    const responseData: IResponseData = {
      success: false,
      error: errorMessage,
      data,
      metadata: {
        timestamp: new Date().toISOString(),
        requestId: this.generateId()
      }
    };

    this.showErrorToast(errorMessage, context || 'Error');
    return responseData;
  }

  /**
   * Handle warning response
   */
  handleWarning(message: string, data?: any, context?: string): IResponseData {
    const responseData: IResponseData = {
      success: true,
      message,
      warnings: [message],
      data,
      metadata: {
        timestamp: new Date().toISOString(),
        requestId: this.generateId()
      }
    };

    this.showWarningToast(message, context);
    return responseData;
  }

  /**
   * Register response handler for specific operations
   */
  registerResponseHandler(operation: string, handler: (response: IResponseData) => void): void {
    this.responseHandlers.set(operation, handler);
  }

  /**
   * Unregister response handler
   */
  unregisterResponseHandler(operation: string): void {
    this.responseHandlers.delete(operation);
  }

  /**
   * Execute response handler for operation
   */
  executeResponseHandler(operation: string, response: IResponseData): void {
    const handler = this.responseHandlers.get(operation);
    if (handler) {
      handler(response);
    }
  }

  // === BUSINESS LOGIC NOTIFICATIONS ===

  /**
   * Show bid-related notifications
   */
  showBidNotification(type: 'success' | 'error' | 'warning' | 'info', message: string, context?: string): void {
    const title = context || 'Bid Operation';
    
    switch (type) {
      case 'success':
        this.showSuccessToast(message, title);
        break;
      case 'error':
        this.showErrorToast(message, title);
        break;
      case 'warning':
        this.showWarningToast(message, title);
        break;
      case 'info':
        this.showInfoToast(message, title);
        break;
    }
  }

  /**
   * Show file operation notifications
   */
  showFileNotification(type: 'success' | 'error' | 'warning' | 'info', message: string, fileName?: string): void {
    const title = fileName ? `File: ${fileName}` : 'File Operation';
    
    switch (type) {
      case 'success':
        this.showSuccessToast(message, title);
        break;
      case 'error':
        this.showErrorToast(message, title);
        break;
      case 'warning':
        this.showWarningToast(message, title);
        break;
      case 'info':
        this.showInfoToast(message, title);
        break;
    }
  }

  /**
   * Show validation notifications
   */
  showValidationNotification(errors: string[], warnings?: string[]): void {
    if (errors.length > 0) {
      this.showErrorNotification('Validation Failed', errors.join('\n'));
    }
    
    if (warnings && warnings.length > 0) {
      this.showWarningNotification('Validation Warnings', warnings.join('\n'));
    }
  }

  /**
   * Show error notification with details
   */
  showErrorNotification(title: string, message: string, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      error: true,
      duration: 0, // Don't auto-close error notifications
      actions
    });
  }

  /**
   * Show warning notification with details
   */
  showWarningNotification(title: string, message: string, actions?: INotificationData['actions']): void {
    this.showNotification({
      open: true,
      title,
      message,
      warning: true,
      duration: 10000, // 10 seconds for warnings
      actions
    });
  }

  // === UTILITY METHODS ===

  /**
   * Add listener for service changes
   */
  addListener(listener: () => void): () => void {
    this.listeners.push(listener);
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
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Clear all notifications and dialogs
   */
  clearAll(): void {
    this.notifications = [];
    this.confirmDialogs = [];
    this.toastNotifications = [];
    this.notifyListeners();
  }

  /**
   * Get service statistics
   */
  getStats(): {
    notifications: number;
    confirmDialogs: number;
    toastNotifications: number;
    listeners: number;
    responseHandlers: number;
  } {
    return {
      notifications: this.notifications.length,
      confirmDialogs: this.confirmDialogs.length,
      toastNotifications: this.toastNotifications.length,
      listeners: this.listeners.length,
      responseHandlers: this.responseHandlers.size
    };
  }
}
