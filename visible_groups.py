from Products.GSContent.view import GSSiteInfo

def get_all_visible_groups(context):
    """Returns the IDs of all groups that are visible to the user in a
    particular context.
    """
    groupsObj = get_groups_object(context)
    allGroups = groupsObj.objectValues(['Folder', 'Folder (Ordered)'])
    
    visibleGroups = []
    for group in allGroups:
        try:
            group.messages.getId()
        except:
            continue
        else:
            visibleGroups.append(group)
    retval = [g.getId() for g in visibleGroups]
    return retval

def visible_groups(groupIds, context):
    """Get the subset of all groups in "groupIds" that are visible.
    """
    visibleGroups = get_all_visible_groups(context)
    retval = [gId for gId in groupIds if gId in visibleGroups]
    return retval

def get_groups_object(context):
    site_root = context.site_root()
    siteInfo = GSSiteInfo(context)
    siteId = siteInfo.get_id()
    site = getattr(getattr(site_root, 'Content'), siteId)
    groupsObj = getattr(site, 'groups')
    
    return groupsObj

