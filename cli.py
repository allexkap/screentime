def color2text(r, g, b, t='  '):
    return f'\033[48;2;{r};{g};{b}m{t}\033[0m'
