from capstone.watson import discovery

supplements = discovery.get_suppliments()

# takes a string that is the concatination of all the passages returned to the user
def get_related_supplements(passages_string):
    related_supps = []
    print('id' in supplements)
    for s in supplements:
        if s != 'id' and (s in passages_string or ' '.join(s.split('-')) in passages_string):
            related_supps.append(s)
    return related_supps
