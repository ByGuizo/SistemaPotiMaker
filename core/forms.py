INPUT_CLASS = (
    'w-full border-2 border-black px-3 py-2 transition-all duration-150 '
    'focus:outline-none focus:shadow-brutal-fuchsia focus:-translate-x-0.5 focus:-translate-y-0.5'
)


class EstiloPotiMakerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existente = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existente} {INPUT_CLASS}'.strip()
