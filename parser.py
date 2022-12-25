import pandas as pd


class Grammar:
    def __init__(self, v_start, grammar):
        self.v_start = v_start
        self.grammar = grammar


def get_n(grammar: list[str]) -> set[str]:
    map_dict = get_dict(grammar)
    n_set = set([key for key in map_dict])
    return n_set


def get_t(grammar: list[str]) -> set[str]:
    n_set = get_n(grammar)
    map_dict = get_dict(grammar)

    t_set = set()
    for line in map_dict.values():
        for string in line:
            for char in string:
                if char not in n_set:
                    t_set.add(char)
    return t_set


# 右侧符号串
def get_r(grammar: list[str]) -> set[str]:
    map_dict = get_dict(grammar)
    r_set = set()
    for line in map_dict.values():
        for string in line:
            r_set.add(string)
    return r_set


def unicode_encode(ch: str) -> str:
    ch_dict = {
        'A': 'Ā',
        'B': 'Ɓ',
        'C': 'Ɔ',
        'D': 'Ɖ',
        'E': 'Ǝ',
        'F': 'Ƒ',
        'T': 'Ƭ'
    }
    return ch_dict[ch]


def unicode_decode(ch: str) -> str:
    ch_dict = {
        'Ā': 'A\'',
        'Ɓ': 'B\'',
        'Ɔ': 'C\'',
        'Ɖ': 'D\'',
        'Ǝ': 'E\'',
        'Ƒ': 'F\'',
        'Ƭ': 'T\''
    }
    if ch in ch_dict.keys():
        return ch_dict[ch]
    return ch


def get_dict_raw(grammar: list[str]) -> dict[str:list[str]]:
    split = [line.split('::=') for line in grammar]
    map_dict_raw = dict(zip([spl[0] for spl in split], [spl[1].split('|') for spl in split]))
    return map_dict_raw


def is_left_recursion(grammar: list[str]) -> dict[str:list[str]]:
    map_dict_raw = get_dict_raw(grammar)
    for key, value in map_dict_raw.items():
        for item in value:
            if item.startswith(key):
                return True
    return False


def get_dict(grammar: list[str]) -> dict[str:list[str]]:
    map_dict_raw = get_dict_raw(grammar)
    map_dict = map_dict_raw.copy()

    if is_left_recursion(grammar):
        for key, value in map_dict_raw.items():
            for item in value:
                if item.startswith(key):

                    map_dict.pop(key)

                    map_dict[key] = []
                    map_dict[unicode_encode(key)] = []

                    for item in value:
                        if item.startswith(key):
                            map_dict[unicode_encode(key)].append(item.lstrip(key) + unicode_encode(key))
                        else:
                            map_dict[key].append(item + unicode_encode(key))
                        if 'ε' not in map_dict[unicode_encode(key)]:
                            map_dict[unicode_encode(key)].append('ε')
        return map_dict
    else:
        return map_dict_raw


def get_first(v: str, map_dict: dict[str:list[str]], t_set: set[str], n_set: set[str]) -> set[str]:
    first_set = set()
    # 单个符号
    if len(v) == 1:
        # 如果是终结符，first集等于自身
        if v in t_set:
            first_set.add(v)
        # 如果是非终结符
        elif v in n_set:
            # 某个右侧符号串
            for string in map_dict[v]:
                # 如果是以终结符开头，将此终结符加入first集
                if string[0] in t_set:
                    first_set.add(string[0])
                # 如果是非终结符
                elif string[0] in n_set:
                    # 递归，将首字符first集中一切非ε符号加入
                    for i in get_first(string[0], map_dict, t_set, n_set):
                        if i != 'ε':
                            first_set.add(i)
                    # 如果有ε，查看下一个符号，循环直到遇到无ε或者规则末
                    count = 0
                    while count < len(string) - 1 and 'ε' in get_first(string[count], map_dict, t_set, n_set):
                        count += 1
                        for i in get_first(string[count], map_dict, t_set, n_set):
                            if i != 'ε':
                                first_set.add(i)
            # 形如x->ε的规则，将ε插入
            if 'ε' in map_dict[v]:
                first_set.add('ε')
    # 符号串
    else:
        string = v
        items_updated = get_first(string[0], map_dict, t_set, n_set)
        items_updated.discard('ε')
        first_set.update(items_updated)
        count = 0
        while count < len(string) - 1 and 'ε' in get_first(string[count], map_dict, t_set, n_set):
            count += 1
            items_updated = get_first(string[count], map_dict, t_set, n_set)
            items_updated.discard('ε')
            first_set.update(items_updated)
        if count == len(string) - 1 and 'ε' in get_first(string[count], map_dict, t_set, n_set):
            first_set.add('ε')
    return first_set


def get_first_dict(grammar: list[str]) -> dict[str:set[str]]:
    map_dict = get_dict(grammar)
    t_set = get_t(grammar)
    n_set = get_n(grammar)
    r_set = get_r(grammar)

    first_dict = dict.fromkeys(n_set)

    for v in t_set.union(n_set).union(r_set):
        first_dict[v] = get_first(v, map_dict, t_set, n_set)

    return first_dict


def get_follow_dict(grammar: list[str], s: str) -> dict[str:set[str]]:
    first_dict = get_first_dict(grammar)
    map_dict = get_dict(grammar)
    n_set = get_n(grammar)
    t_set = get_t(grammar)

    follow_dict = dict.fromkeys(n_set)
    for n in n_set:
        follow_dict[n] = set()

    # 规则1
    follow_dict[s].add('#')

    # 规则2
    changed = True
    while changed:
        changed = False

        for key, value in map_dict.items():
            for string in value:
                for i in range(len(string) - 1):
                    if string[i] in n_set:
                        # 将first(β)中的一切符号加入Follow(B)中
                        for char in get_first(string[i + 1:], map_dict, t_set, n_set):
                            if char not in follow_dict[string[i]] and char != 'ε':
                                follow_dict[string[i]].add(char)
                                changed = True

                        # 规则3(A::=αBβ型)
                        flag = True

                        # β能推导出ε
                        for j in range(i + 1, len(string)):
                            if 'ε' not in first_dict[string[j]]:
                                flag = False
                        if flag:
                            # 将follow(A)中的全部终结符加入follow(B)
                            for follow_item in follow_dict[key]:
                                if follow_item not in follow_dict[string[i]]:
                                    follow_dict[string[i]].add(follow_item)
                                    changed = True
                # 规则3(A::=αB型)
                if string[len(string) - 1] in n_set:
                    # 将follow(A)中的全部终结符加入follow(B)
                    for follow_item in follow_dict[key]:
                        if follow_item not in follow_dict[string[len(string) - 1]]:
                            follow_dict[string[len(string) - 1]].add(follow_item)
                            changed = True

    return follow_dict


def get_table(grammar_class: Grammar) -> pd.DataFrame:
    n = get_n(grammar_class.grammar)
    t = get_t(grammar_class.grammar)
    get_r(grammar_class.grammar)
    map_dict = get_dict(grammar_class.grammar)
    first = get_first_dict(grammar_class.grammar)
    follow = get_follow_dict(grammar_class.grammar, grammar_class.v_start)

    # 打表
    index = list(n)
    columns = list(t)
    if 'ε' in columns:
        columns.remove('ε')
    columns.append('#')

    # 默认置为错误
    df = pd.DataFrame(data='[!]', index=index, columns=columns)

    for key, value in map_dict.items():
        for string in value:
            # 规则1
            if string != 'ε':
                for a in first[string]:
                    df[a][key] = f'{key}::={string}'
            # 规则2
            if 'ε' in first[string]:
                for b in follow[key]:
                    df[b][key] = f'{key}::={string}'
    df = df[sorted(df.columns)]
    df = df.sort_index()
    return df


def parser(grammar_class: Grammar, string: str) -> (bool, list[int, str, str, str]):
    """返回一个元组，第 0 项为是否出错，第二项为完整的分析过程"""
    t = get_t(grammar_class.grammar)
    table = get_table(grammar_class)
    # 分析栈
    stack = '#' + grammar_class.v_start
    # 余留输入栈
    string = string + '#'
    # 分析过程
    record = []
    # 分析过程的序号
    index = 1
    # 直到分析栈为空
    while stack[-1] != '#':
        # 如果分析栈最后的符号是终结符
        if stack[-1] in t:
            # 该终结符匹配成功
            if stack[-1] == string[0]:
                # 添加分析过程
                record.append([index, stack, string, '[Match]'])
                index += 1
                # stack 和 string pop栈顶元素
                stack = stack[:-1]
                string = string[1:]
            # 该终结符匹配失败，添加匹配失败信息，返回
            else:
                record.append([index, stack, string, '[Error]'])
                return False, record
        # 存在移进规则
        if table[string[0]][stack[-1]] != '[!]':
            # 移进
            record.append([index, stack, string, table[string[0]][stack[-1]]])
            index += 1
            right = table[string[0]][stack[-1]].split('::=')[1]
            stack = stack[:-1]
            if right != 'ε':
                stack += right[::-1]
        # 不存在移进规则，出错
        else:
            record.append([index, stack, string, '[Error]' + f'  Reason: ({stack[-1]},{string[0]})==[!]'])
            return False, record
    # 两栈顶都为#，匹配成功
    if stack[-1] == '#' and string[0] == '#':
        record.append([index, stack, '#', '[Success]'])
        return True, record
    # 栈顶有余留符号，匹配失败
    else:
        record.append([index, '#', string, '[Error]' + f'  Reason: (#,{string[0]})==[!]'])
        return False, record


if __name__ == '__main__':
    g = Grammar(v_start='E',
                grammar=['E::=E+T|T',
                         'T::=T*F|F',
                         'F::=(E)|i']
                )

    print(f'G[{g.v_start}]:\n\t', g.grammar, end='\n\n')

    print('Raw Dict:\n\t', get_dict_raw(g.grammar), end='\n\n')
    print('Dict:\n\t', get_dict(g.grammar), end='\n\n')

    print('Vn:\n\t', get_n(g.grammar), end='\n\n')
    print('Vt:\n\t', get_t(g.grammar), end='\n\n')
    print('Vr:\n\t', get_r(g.grammar), end='\n\n')

    # 消除左递归的格式化输出

    if is_left_recursion(g.grammar):
        for key, value in get_dict(g.grammar).items():
            for ch in key:
                print(unicode_decode(ch), end='::=')
            for item in value:
                for ch in item:
                    print(unicode_decode(ch), end='')
                print('|', end='')
            print('\b')


    print('First dict:\n\t', get_first_dict(g.grammar), end='\n\n')
    print('Follow dict:\n\t', get_follow_dict(g.grammar, g.v_start), end='\n\n')
    print('Table:\n', get_table(g), end='\n\n')

    print('First:')
    for key, value in get_first_dict(g.grammar).items():
        print(f'\'{key}\':{value}')
    print()

    print('Follow:')
    for key, value in get_follow_dict(g.grammar, g.v_start).items():
        print(f'\'{key}\':{value}')
    print()
    string_tested = '(i+i(*i)'
    is_successful, procedure = parser(grammar_class=g, string=string_tested)

    print(f'String tested: {string_tested}\n' + 'The test is ' + ('[Successful]' if is_successful else '[Failed]'))
    print('Procedure:')
    for line in procedure:
        print('{0:^10} {1:<10} {2:>10}    {3:<10}'.format(line[0], line[1], line[2], line[3]))
