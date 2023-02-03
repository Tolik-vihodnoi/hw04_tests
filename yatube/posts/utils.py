from django.core.paginator import Paginator


def do_page_obj(request, q_set, num_of_items):
    page_num = request.GET.get('page')
    paginator = Paginator(q_set, num_of_items)
    return paginator.get_page(page_num)
