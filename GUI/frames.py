from GUI import connection_frame, delay_frame, search_frame, search_results_frame, websites_list_frame


class Frames:
    def __init__(self, data):
        self.connection_frame = connection_frame.ConnectionFrame(master=data.master, corner_radius=0)
        self.delay_frame = delay_frame.DelayFrame(data=data, corner_radius=0)
        self.search_frame = search_frame.SearchFrame(master=data.master, corner_radius=0)
        self.search_results_frame = search_results_frame.SearchResultsFrame(data=data, corner_radius=0)
        self.websites_list_frame = websites_list_frame.WebsitesListFrame(data=data, corner_radius=0)
