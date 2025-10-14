# Dashboard Sections CSS Documentation

This CSS file provides enhanced styling for the new dashboard sections: Weekly Collections, Weekly Revenue Lost, and Debtors.

## Features

### 1. Dashboard Section Containers
- **`.dashboard-section`**: Base styling for all dashboard sections
- **`.weekly-collections-section`**: Green-themed styling for collections data
- **`.weekly-revenue-lost-section`**: Red-themed styling for revenue lost data  
- **`.debtors-section`**: Purple-themed styling for debtor categories

### 2. Table Styling
- **`.editable-table`**: Enhanced table styling with proper borders and spacing
- **`.dashboard-section-header`**: Consistent header styling across sections
- **`.table-container`**: Container with proper overflow handling

### 3. Interactive Elements
- **`.editable-cell`**: Clickable cells with hover effects and edit indicators
- **`.non-editable-cell`**: Read-only cells (like auto-calculated totals)
- **`.inline-edit-input`**: Styled input fields for inline editing
- **`.cell-tooltip`**: Tooltip functionality for additional context

### 4. Visual Feedback States
- **`.cell-loading`**: Loading spinner animation during save operations
- **`.cell-success`**: Green flash animation for successful saves
- **`.cell-error`**: Red shake animation for errors
- **`.input-error-message`**: Inline error message styling

### 5. Value-Specific Styling
- **`.currency-value`**: Green styling for currency amounts
- **`.mwh-value`**: Red styling for MWh values
- **`.percentage-value`**: Purple styling for percentage values
- **`.auto-calculated`**: Gray styling for auto-calculated fields

### 6. Responsive Design
- **Tablet (≤768px)**: 2-column grid layout, smaller fonts
- **Mobile (≤480px)**: Single column layout, horizontal scroll for tables
- **Touch-friendly**: Larger touch targets, optimized hover effects

### 7. Accessibility Features
- High contrast mode support
- Reduced motion support for users with motion sensitivity
- Proper focus indicators
- Screen reader friendly tooltips

## Usage

### Basic Section Structure
```html
<div class="dashboard-section weekly-collections-section">
  <div class="dashboard-section-header">
    💰 Weekly Collections
  </div>
  <div class="table-container">
    <table class="editable-table">
      <!-- table content -->
    </table>
  </div>
</div>
```

### Editable Cell
```html
<td class="editable-cell currency-value" data-tooltip="Click to edit">
  5.2M
</td>
```

### Non-Editable Cell
```html
<td class="non-editable-cell auto-calculated" data-tooltip="Auto-calculated">
  205.7 MWh
</td>
```

### Inline Edit Input
```html
<input type="text" class="inline-edit-input" value="5.2" placeholder="Enter amount">
```

## JavaScript Integration

The CSS classes are designed to work with the React dashboard component:

```javascript
// Show loading state
cell.classList.add('cell-loading');

// Show success state
cell.classList.add('cell-success');
setTimeout(() => cell.classList.remove('cell-success'), 2000);

// Show error state
cell.classList.add('cell-error');
```

## Browser Support

- Modern browsers (Chrome 60+, Firefox 55+, Safari 12+, Edge 79+)
- CSS Grid and Flexbox support required
- CSS Custom Properties (variables) support required

## Testing

Use `dashboard_sections_test.html` to test all styling features:
- Visual appearance of all section types
- Interactive states (hover, loading, success, error)
- Responsive behavior
- Inline editing interface
- Accessibility features

## Customization

The CSS uses CSS custom properties for easy theming:

```css
:root {
  --collections-primary: #22c55e;
  --revenue-lost-primary: #ef4444;
  --debtors-primary: #9333ea;
}
```

## Performance

- Uses CSS transforms for animations (GPU accelerated)
- Minimal repaints with efficient selectors
- Optimized for 60fps animations
- Lazy loading compatible