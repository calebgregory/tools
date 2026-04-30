import argh

from slacktools.lists import cli as lists
from slacktools.users import cli as users


def main() -> None:
    parser = argh.ArghParser()

    app = {
        "lists": [lists.discover, lists.columns, lists.ls, lists.add],
        "users": [users.find, users.sync, users.info],
    }
    for group_name, commands in app.items():
        argh.add_commands(parser, commands, group_name=group_name)

    argh.dispatch(parser)


if __name__ == "__main__":
    main()
