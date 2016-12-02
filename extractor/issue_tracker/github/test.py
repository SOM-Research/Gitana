__author__ = 'valerio cosentino'

from github import Github

def x():

    recover_times = 200000
    lenght = 1000

    x = 5
    while lenght > 0:
        if lenght % recover_times == 0:
            x = lenght / recover_times
            print str(x)
        lenght -= 1


def main():
    x()
    # github = Github("5ed4abfa9db99b61d1b1159dff548571e1bee27d")
    # found = None
    # users = github.search_users("gabrielecirulli", **{"type": "user", "in": "login"})
    #
    # for user in users:
    #     found = user
    #     break
    #
    # return found

if __name__ == "__main__":
    main()