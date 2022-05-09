from django.core.paginator import Paginator

NUM_OF_PUBLICATIONS: int = 10


def paginate_page(request, post_list):
    paginator = Paginator(post_list, NUM_OF_PUBLICATIONS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
