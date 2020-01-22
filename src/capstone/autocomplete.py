# https://leetcode.com/problems/design-search-autocomplete-system/

############################
#
#
#
#
#
# https://cloud.ibm.com/apidocs/discovery?code=python#get-autocomplete-suggestions
#
#
#
#
#
#####################


class AutocompleteSystem:
    def __init__(self, sentences: List[str], times: List[int]):
        self.hot = collections.defaultdict(int)
        self.top3 = collections.defaultdict(list)
        for i in range(len(times)):
            s = sentences[i]
            self.hot[sentences[i]] = times[i] - 1
            self.addOrUpdate(s)
        self.cur = ""

    def addOrUpdate(self, s):
        self.hot[s] += 1
        cur = ""
        for c in s:
            cur += c
            q = self.top3[cur]
            if s not in q:
                q.append(s)
            self.top3[cur] = sorted(q, key=lambda x: [-self.hot[x], x])[:3]

    def input(self, c: str) -> List[str]:
        if c == "#":
            self.addOrUpdate(self.cur)
            self.cur = ""
            return []
        self.cur += c
        return self.top3[self.cur]
