# Release Notes - Version 3.1.0
**Release Date:** June 15, 2025

## 🎯 **Major Enhancement: Non-Scrollable Account Input Fields**

### **Problem Solved**
Fixed a critical usability issue where users could accidentally change account selections in both single and bulk entry forms by scrolling the mouse wheel over combo boxes. This was particularly problematic in accounting applications where accuracy is paramount.

### **New Features**

#### 🛡️ **NonScrollableComboBox Implementation**
- **Custom Widget**: New `NonScrollableComboBox` class that prevents accidental scrolling
- **Smart Behavior**: Only allows wheel scrolling when the combo box is focused AND dropdown is open
- **Universal Application**: Applied to all debit and credit account selection fields

#### 📝 **Enhanced Journal Entry**
- **Protected Fields**: Debit and credit account combo boxes now ignore accidental mouse wheel scrolling
- **Preserved Functionality**: Normal dropdown navigation still works when intentionally used
- **Improved UX**: Users can safely scroll through forms without fear of changing account selections

#### 📊 **Enhanced Bulk Entry**
- **Table-wide Protection**: All account selection combo boxes in the bulk entry table are now scroll-protected
- **Consistent Behavior**: Same protection applied to both existing rows and newly added rows
- **Maintained Performance**: No impact on data entry speed or functionality

### **Technical Implementation**

#### **Files Modified:**
- `src/ui/components/widgets.py` - Added `NonScrollableComboBox` class
- `src/ui/pages/journal.py` - Updated debit/credit fields to use new widget
- `src/ui/pages/bulk_entry.py` - Updated all account combo boxes

#### **Widget Behavior:**
- **Default State**: Mouse wheel scrolling is ignored
- **Focused + Closed Dropdown**: Mouse wheel scrolling is ignored  
- **Focused + Open Dropdown**: Mouse wheel scrolling works normally
- **All Other Functionality**: Unchanged (clicking, typing, keyboard navigation)

### **Quality Assurance**
- ✅ All imports verified working
- ✅ No compilation errors
- ✅ Application functionality maintained
- ✅ Comprehensive testing completed
- ✅ Documentation provided

### **User Benefits**
1. **Accident Prevention**: No more unintentional account changes while scrolling
2. **Data Accuracy**: Reduced risk of posting to wrong accounts
3. **Improved Confidence**: Users can scroll freely without worry
4. **Professional Experience**: More robust and reliable accounting interface

### **Backward Compatibility**
- ✅ Full backward compatibility maintained
- ✅ No breaking changes to existing functionality
- ✅ All existing data and workflows preserved
- ✅ Styling and appearance unchanged

---

## 📋 **Version Comparison**

| Feature | v3.0.0 | v3.1.0 |
|---------|--------|--------|
| Journal Entry | ✅ | ✅ |
| Bulk Entry with CSV/Excel Import | ✅ | ✅ |
| Transaction History Display | ✅ | ✅ |
| Clean UI without Background Boxes | ✅ | ✅ |
| **Non-Scrollable Account Fields** | ❌ | ✅ **NEW** |

---

## 🚀 **Upgrade Instructions**
This is a seamless upgrade with no user action required. The new scroll protection is automatically active for all account selection fields.

## 💡 **Usage Tips**
- **Normal Use**: Click on account combo boxes and select as usual
- **Dropdown Navigation**: Click to focus, then use mouse wheel to scroll through options
- **Form Scrolling**: Scroll freely through forms without affecting account selections
- **Bulk Entry**: Same protection applies to all rows in the bulk entry table

---

**Previous Release:** [v3.0.0](RELEASE_v3.0.0.md)
