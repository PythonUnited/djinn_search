from haystack.inputs import AutoQuery, Clean, Exact, Not


def split_query(query_string, query_obj):

    """ Split a query into it's separate parts. This uses the same
    code as haystack.inputs.AutoQuery. Except for one line... """

    exacts = AutoQuery.exact_match_re.findall(query_string)
    tokens = []
    query_bits = []

    for rough_token in AutoQuery.exact_match_re.split(query_string):
        if not rough_token:
            continue
        elif not rough_token in exacts:
            # We have something that's not an exact match but may have more
            # than on word in it.
            tokens.extend(rough_token.split(' '))
        else:
            tokens.append(rough_token)

    for token in tokens:
        if not token:
            continue
        if token in exacts:
            query_bits.append(Exact(token, clean=True).prepare(query_obj))
        elif token.startswith('-') and len(token) > 1:
            # This might break Xapian. Check on this.
            query_bits.append(Not(token[1:]).prepare(query_obj))
        else:
            query_bits.append(Clean(token).prepare(query_obj))

    return query_bits
