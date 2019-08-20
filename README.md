# pyqt_subclasses
PyQt Widgets sub-classes

### custom_qtreewidget
---
* Only allows 1-tier sub-menu
* Item dialog for creation of parent/ child items

* Derive list items, and return in dictionary format (`defaultdict(list))`
    - All items
    - Only checked items
    - Only uncheck items
* Derive number of child items in parent

* Added in signal - `itemToggled`
    - Allows tracking whenever list item is checked or unchecked
* Added in context menu
    - Different menu options when right-clicking on parent/ child list item
    - Parent-menu: 'Remove Item' + 'Add new sub item'
    - Child-menu: 'Remove Item'
* Added in `CustomTreeDelegate`, with the use of `IsNewItemRole` that allows User to toggle/ highlight the newly added item(s) - Applies to both parent and child items.
* Added in Maya visual hacks to make the checkboxes more visible so that the
checkbox outline does not blends in with the background


### custom_listwidget
