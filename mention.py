"""detecting mentions"""
import re

def strip_space(c):
    if re.match(r'(\W+)', c) is not None:
        c = re.sub('[\r\n]', '', c)
        if len(c) == 0:
            c = ' '
    return c

def greedy_detector(db, text, allcase=False):
    cand = None
    offset = 0
    curr = ''
    mentions = []
    total_match = False
    match_i = 0
    tokens = re.split(r'(\W+)', text) + ['xxxxxnotexist']
    i, l_tk = 0, len(tokens)
    while i < l_tk:
        c = tokens[i]
        if cand is None:
            curr = c
        else:
            curr += strip_space(c)

        if re.match(r'(\W+)', c) is None and len(c) > 0:
            title_exist = False
            curr_titles = db.gen_texts(curr, allcase)
            for title in curr_titles:
                if db.title_exist(title):
                    title_exist = True
                    break
            if title_exist:
                end_offset = offset+len(c.encode('utf8'))
                l_total_match = False
                for title in curr_titles:
                    if db.title_match(title):
                        l_total_match = True
                        break

                if cand is None:
                    cand = (curr, offset, end_offset)
                    match_i = i
                elif not total_match or l_total_match:
                    cand = (curr, cand[1], end_offset)
                    match_i = i

                if l_total_match:
                    total_match = True
            else:
                if cand is not None:
                    if total_match:
                        mentions.append(cand)
                    offset = cand[2]
                    c = ''
                    cand = None
                    total_match = False
                    i = match_i
        offset += len(c.encode('utf8'))
        i += 1

    if cand is not None:
        mentions.append(cand)
    return mentions
