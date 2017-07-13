from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': '',
            'host': 'mmopuru-service',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("papyrus_db")

    g.create_project("papyrus_db", "papyrus")
    g.extract_dependency_relations("papyrus_db", "papyrus", "papyrus_repo", "C:\\mmopuru\\Gitana")

if __name__ == "__main__":
    main()