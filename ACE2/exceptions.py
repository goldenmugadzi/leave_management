"""
Custom exceptions for ACE2 reporting system
"""

class ACEReportException(Exception):
    """Base exception for ACE reporting errors"""
    pass

class BudgetDataError(ACEReportException):
    """Exception raised when budget data is invalid or missing"""
    pass

class ReportGenerationError(ACEReportException):
    """Exception raised when report generation fails"""
    pass

class DataValidationError(ACEReportException):
    """Exception raised when data validation fails"""
    pass

class ExportError(ACEReportException):
    """Exception raised when export operations fail"""
    pass

class PermissionError(ACEReportException):
    """Exception raised when user lacks permission for operation"""
    pass
