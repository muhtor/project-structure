from apps.core.api.renderers import CoreJSONRenderer

class UserJSONRenderer(CoreJSONRenderer):
    object_label = 'user'

    # def render(self, data, media_type=None, render_context=None):
    #     token = data.get('token', None)

    #     if token is not None and isinstance(token, bytes):
    #         data['token'] = token.decode('utf-8')
            
    #     return super(UserJSONRenderer, self).render(data)
