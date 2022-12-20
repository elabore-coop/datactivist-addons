from operator import itemgetter
from collections import OrderedDict
from odoo import http,_
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem
from odoo.osv.expression import OR

class CustomerPortalDeliverables(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'deliverables_count' in counters:
            domain = self._get_deliverables_domain()
            values['deliverables_count'] = request.env['project.task'].search_count(domain) if request.env['project.task'].check_access_rights('read', raise_exception=False) else 0
        return values

    def _get_deliverables_domain(self, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, searchbar_filters=None ):
        # default searchbar_filters value
        if not searchbar_filters:
            searchbar_filters = {
            'all': {'label': _('All'), 'domain': ("active", "=", True)},
        }

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = [searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']]

        # default group by value
        if not groupby:
            groupby = 'project'

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            if search_in in ('project', 'all'):
                search_domain = OR([search_domain, [('project_id', 'ilike', search)]])
            domain += search_domain

        # Deliverables only
        domain.append(('tag_ids', '=', request.env.ref('datactivist_deliverable_portal_filter.task_tag_deliverable').id))
        return domain

    @http.route(['/my/deliverables', '/my/deliverables/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_deliverables(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id, project_id'},
            'project': {'label': _('Project'), 'order': 'project_id, stage_id'},
            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': ("active", "=", True)},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'stage': {'input': 'stage', 'label': _('Search in Stages')},
            'project': {'input': 'project', 'label': _('Search in Project')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'project': {'input': 'project', 'label': _('Project')},
            'stage': {'input': 'stage', 'label': _('Stage')},
        }

        # extends filterby criteria with project the customer has access to
        projects = request.env['project.project'].search([])
        for project in projects:
            searchbar_filters.update({
                str(project.id): {'label': project.name, 'domain': [('project_id', '=', project.id)]}
            })

        # extends filterby criteria with project (criteria name is the project id)
        # Note: portal users can't view projects they don't follow
        project_groups = request.env['project.task'].read_group([('project_id', 'not in', projects.ids)],
                                                                ['project_id'], ['project_id'])
        for group in project_groups:
            proj_id = group['project_id'][0] if group['project_id'] else False
            proj_name = group['project_id'][1] if group['project_id'] else _('Others')
            searchbar_filters.update({
                str(proj_id): {'label': proj_name, 'domain': [('project_id', '=', proj_id)]}
            })

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'all'
        # domain = searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

        # default group by value
        if not groupby:
            groupby = 'project'

        # if date_begin and date_end:
        #     domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # # search
        # if search and search_in:
        #     search_domain = []
        #     if search_in in ('content', 'all'):
        #         search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
        #     if search_in in ('customer', 'all'):
        #         search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
        #     if search_in in ('message', 'all'):
        #         search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
        #     if search_in in ('stage', 'all'):
        #         search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
        #     if search_in in ('project', 'all'):
        #         search_domain = OR([search_domain, [('project_id', 'ilike', search)]])
        #     domain += search_domain

        # # Deliverables only
        # tag = request.env["project.tags"].search(["id", "=", "task_tag_deliverable"], limit=1)
        # domain += [("tag_ids", "in", [tag])]

        domain = self._get_deliverables_domain(date_begin, date_end, sortby, filterby, search, search_in, groupby, searchbar_filters)

        # task count
        task_count = request.env['project.task'].search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/deliverables",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=task_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        if groupby == 'project':
            order = "project_id, %s" % order  # force sort on project first to group by project in view
        elif groupby == 'stage':
            order = "stage_id, %s" % order  # force sort on stage first to group by stage in view

        tasks = request.env['project.task'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_tasks_history'] = tasks.ids[:100]

        if groupby == 'project':
            grouped_tasks = [request.env['project.task'].concat(*g) for k, g in groupbyelem(tasks, itemgetter('project_id'))]
        elif groupby == 'stage':
            grouped_tasks = [request.env['project.task'].concat(*g) for k, g in groupbyelem(tasks, itemgetter('stage_id'))]
        else:
            grouped_tasks = [tasks]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_deliverables': grouped_tasks,
            'page_name': 'deliverable',
            'default_url': '/my/deliverables',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("datactivist_deliverable_portal_filter.portal_my_deliverables", values)