from django import template

register = template.Library()

@register.filter
def cpf(value):
    if value:
        # Remove qualquer caractere que não seja número
        v = ''.join(filter(str.isdigit, str(value)))
        # Preenche com zeros à esquerda até ter 11 dígitos
        v = v.zfill(11)
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    return value

@register.filter
def telefone(value):
    """Formata telefone como (00) 0000-0000 ou (00) 00000-0000"""
    if value:
        v = ''.join(filter(str.isdigit, value))
        if len(v) == 10:
            return f"({v[:2]}) {v[2:6]}-{v[6:]}"
        elif len(v) == 11:
            return f"({v[:2]}) {v[2:7]}-{v[7:]}"
    return value

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
