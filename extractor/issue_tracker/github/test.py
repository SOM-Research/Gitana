__author__ = 'valerio cosentino'

from github import Github

TOKEN = 'YOUR-TOKEN'

def get_issue_events(repo):
    page_count = 1
    last_page = int(repo.get_issues(state="all", direction="asc")._getLastPageUrl().split("page=")[-1])

    while page_count != last_page:
        issues = repo.get_issues(state="all").get_page(page_count)
        for i in issues:
            if i.number == 25:
                print i.title + " -- #" + str(i.number)

                assignee = i.assignee
                if assignee:
                    print "assignee: " + assignee._identity

                events = i.get_events()
                for e in events:
                    actor = e.actor
                    login = actor._identity
                    created_at = e.created_at
                    event = e.event

                    print "login: " + str(login) + " --- created_at:" + str(created_at) + " --- event: " + str(event)

                    if event == 'labeled':
                        label = e._rawData.get('label').get('name')
                        print label

                    if event == 'assigned':
                        assignee = e._rawData.get('assignee').get('login')
                        assigner = e._rawData.get('assigner').get('login')
                        print "assignee: " + assignee + " --- assigner: " + assigner

                    if event == 'mentioned':
                        found = [c for c in i.get_comments() if c.created_at == created_at]

                        if len(found) == 1:
                            creator = found[0].user.login
                            print "creator " + creator + " mentioned " + login
                        else:
                            print "comments with same creation time should not exist!"

                    if event == 'subscribed':
                        print login + " subscribed to the issue"

                    #other events to map

        page_count += 1


def main():

    g = Github(TOKEN)
    repo = g.get_repo("gabrielecirulli/2048")

    get_issue_events(repo)

if __name__ == "__main__":
    main()