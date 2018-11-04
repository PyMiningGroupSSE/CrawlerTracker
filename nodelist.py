class NodeList:
    __nodelist__ = None

    def __init__(self):
        self.__nodelist__ = list()

    def append(self, node_info):
        if type(node_info) is not NodeInfo:
            raise TypeError("param must be type of NodeInfo")
        self.__nodelist__.append(node_info)

    def remove(self, node_id):
        for node_info in self.__nodelist__:
            if node_info.get_id() == node_id:
                self.__nodelist__.remove(node_info)

    def get_node(self, node_id):
        for node_info in self.__nodelist__:
            if node_info.get_id() == node_id:
                return node_info

    def get_list(self):
        nodelist = list()
        for node_info in self.__nodelist__:
            nodelist.append(node_info.get_all())
        return nodelist

    def get_dict(self):
        nodedict = dict()
        for node_info in self.__nodelist__:
            nodedict[node_info.get_id()] = node_info.get_all()
        return nodedict

    def get_ids(self):
        id_list = list()
        for node_info in self.__nodelist__:
            id_list.append(node_info.get_id())
        return id_list


class NodeInfo:
    __id__ = None
    __ip__ = None
    __cnt__ = None

    def __init__(self, node_id, node_ip):
        self.__id__ = node_id
        self.__ip__ = node_ip
        self.__cnt__ = 0

    def add_count(self, count):
        self.__cnt__ += count

    def get_id(self):
        return self.__id__

    def get_ip(self):
        return self.__ip__

    def get_count(self):
        return self.__cnt__

    def get_all(self):
        return dict(
            id=self.__id__,
            ip=self.__ip__,
            count=self.__cnt__
        )


