from tortoise import Tortoise, connections, fields, run_async
from tortoise.exceptions import OperationalError
from tortoise.models import Model

from dotenv import load_dotenv
import os

load_dotenv()


class Tournament(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()

    def __str__(self):
        return self.name

    class Meta:
        app = "tournaments"


class Event(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    tournament_id = fields.IntField()
    # Here we make link to events.Team, not models.Team
    participants: fields.ManyToManyRelation["Team"] = fields.ManyToManyField(
        "events.Team", related_name="events", through="event_team"
    )

    def __str__(self):
        return self.name

    class Meta:
        app = "events"


class Team(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()

    event_team: fields.ManyToManyRelation[Event]

    def __str__(self):
        return self.name

    class Meta:
        app = "events"


async def run():
    await Tortoise.init(
        {
            "connections": {
                "first": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": os.getenv("PG_HOST"),
                        "port": os.getenv("PG_PORT"),
                        "user": os.getenv("PG_USER"),
                        "password": os.getenv("PG_PASSWORD"),
                        "database": os.getenv("DATABASE_LOCAL"),
                    },
                },
                "second": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": os.getenv("PG_HOST"),
                        "port": os.getenv("PG_PORT"),
                        "user": os.getenv("PG_USER"),
                        "password": os.getenv("PG_PASSWORD"),
                        "database": os.getenv("DATABASE_RETENTION"),
                    },
                },
            },
            "apps": {
                "tournaments": {"models": ["__main__"], "default_connection": "first"},
                "events": {"models": ["__main__"], "default_connection": "second"},
            },
        }
    )
    await Tortoise.generate_schemas()
    client = connections.get("first")
    second_client = connections.get("second")

    tournament = await Tournament.create(name="Tournament")
    await Event(name="Event", tournament_id=tournament.id).save()

    try:
        await client.execute_query('SELECT * FROM "event"')
    except OperationalError:
        print("Expected it to fail")
    results = await second_client.execute_query('SELECT * FROM "event"')
    print(results)


if __name__ == "__main__":
    run_async(run())
