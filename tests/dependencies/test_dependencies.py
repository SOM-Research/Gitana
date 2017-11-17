from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcf_audit_db")

    g.create_project("vcf_audit_db", "vcf_audit")
    g.extract_dependency_relations("vcf_audit_db", "vcf_audit", "vcf_audit_repo", "C:\\mmopuru\\vcf-audit",
                                   extra_paths=[
                                       "C:\\mmopuru\\vcf-audit\\vcf-audit-compliance\\src\\main\\java",
                                       "C:\\mmopuru\\vcf-audit\\vcf-common-operations\\src\\main\\java",
                                       "C:\\mmopuru\\vcf-audit\\support\\gobuild"
                                   ])


if __name__ == "__main__":
    main()
