from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, CatItem, User

engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False},
                       echo=True)
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete Categories if exisitng.
session.query(Category).delete()
# Delete Items if exisitng.
session.query(CatItem).delete()
# Delete Users if exisitng.
session.query(User).delete()

# Create dummy user
User1 = User(name="Amr",
             email="Amr@udacity.com",
             picture='https://pbs.twimg.com/profile_images/'
                     '2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Create dummy data

cat1 = Category(name="Massively Multiplayer Online (MMO)",user_id=1)
session.add(cat1)
session.commit()

catItem1 = CatItem(name="World of Warcraft",
                     description="Since its release, the game has become the most popular"
                                 "and subscribed MMORPG ever with more than 5 million subscribers."
                                 "In the game, players control a character from either the "
                                 "first- or third-person perspective and begin exploring the game "
                                 "world completing quests, interacting with other characters, "
                                 "and fighting all sorts of monsters from the WarCraft universe.",
                     category=cat1)

session.add(catItem1)
session.commit()


catItem2 = CatItem(name="Guild Wars 2",
                     description="The game features a unique aspect in which the game's storyline "
                                 "adjusts based on actions taken by player characters. "
                                 "In it, players create a character based on one of five "
                                 "races and eight character classes or professions.",
                     category=cat1)



session.add(catItem2)
session.commit()


catItem3 = CatItem(name="Star Wars: The Old Republic",
                     description="is a massively multiplayer online roleplaying game "
                                 "set in the Star Wars universe where players create a character "
                                 "and join one of two factions the Galactic Republic or the "
                                 "Sith Empire and choose between the light "
                                 "and dark side of the force within each faction.",
                     category=cat1)



session.add(catItem3)
session.commit()


cat2 = Category(name="Simulations",user_id=1)
session.add(cat2)
session.commit()

catItem4 = CatItem(name="Farming Simulator 19",
                     description="When it comes to farming simulator games, look no further than, er, "
                                 "Farming Simulator 19. The clue’s in the name, frankly. "
                                 "Please excuse our facetiousness, but believe us when we say that "
                                 "if you’re looking for the closest one-to-one recreation of truly "
                                 "living off the land, Giants Software’s latest agricultural outing "
                                 "is for you. And we’re experts, as our Farming ",
                     category=cat2)

session.add(catItem4)
session.commit()


catItem5 = CatItem(name="Flight Simulator X",
                     description="When people say the word ‘simulator,’ Microsoft’s imperious and"
                                 " encyclopaedic aviation behemoth is the first game that springs to "
                                 "mind. It’s inevitable – like picturing a Christian Bale in a clear "
                                 "raincoat flecked with blood whenever you hear "
                                 "Huey Lewis and the News.",
                     category=cat2)

session.add(catItem5)
session.commit()

cat3 = Category(name="Real-Time Strategy (RTS)",user_id=1)
session.add(cat3)
session.commit()

catItem6 = CatItem(name="Company of Heroes ",
                     description="Company of Heroes is an award-winning RTS series that features "
                                 "a World War II setting. Relic, the studio behind the game, "
                                 "focused on building the game's realism based on historical "
                                 "locations and even how soldiers interact.",
                     category=cat3)

session.add(catItem6)
session.commit()


catItem7 = CatItem(name="Age of Empires III",
                     description="Unlike other real-time strategy games on the list, "
                                 "Age of Empires III features real life countries with actual "
                                 "historical military units like samurais. You start off with "
                                 "a civilization that has to go through the dark ages, "
                                 "researching technologies and then eventually opening up "
                                 "trade routes. From there, you’ll build up a "
                                 "massive army to take over parts of Europe and Asia.",
                     category=cat3)

session.add(catItem7)
session.commit()


catItem8 = CatItem(name="The battle for Middle-earth",
                     description="This Strategy game is directly taken from the film Peter Jackson, "
                                 "The Lord of the Rings, this game will bring an amazing battle "
                                 "that will make you irresponsible to play with it. "
                                 "In addition to graphics and an interesting story, the games "
                                 "created by EA Lost Angeles are really "
                                 "suitable for you to play.",
                     category=cat3)

session.add(catItem8)
session.commit()


print("added category items!")

categories = session.query(User).all()
for category in categories:
    print ("User: " + category.name)
    print ("id: "+ str(category.id))
session.query(User).all()

