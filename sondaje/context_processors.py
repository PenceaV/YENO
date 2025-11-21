def guest_status(request):
    
    return {
        'is_guest': request.session.get('is_guest', False)
    }

