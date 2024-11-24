import csv
import sys
import logging
from util import Node, StackFrontier, QueueFrontier

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Maps names to a set of corresponding person_ids
names = {}

# Maps person_ids to a dictionary of: name, birth, movies (a set of movie_ids)
people = {}

# Maps movie_ids to a dictionary of: title, year, stars (a set of person_ids)
movies = {}


def load_data(directory):
    """
    Load data from CSV files into memory.
    """
    logging.info(f"Loading data from directory: {directory}")

    # Load people
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set()
            }
            if row["name"].lower() not in names:
                names[row["name"].lower()] = {row["id"]}
            else:
                names[row["name"].lower()].add(row["id"])
    
    logging.info("Loaded people data.")

    # Load movies
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set()
            }

    logging.info("Loaded movies data.")

    # Load stars
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                logging.warning(f"KeyError when adding star: {row}")
                pass
    
    logging.info("Loaded stars data.")


def main():
    if len(sys.argv) > 2:
        sys.exit("Usage: python degrees.py [directory]")
    
    directory = sys.argv[1] if len(sys.argv) == 2 else "large"

    # Load data from files into memory
    logging.info("Loading data...")
    load_data(directory)
    logging.info("Data loaded.")

    source = person_id_for_name(input("Name: "))
    if source is None:
        logging.error("Person not found.")
        sys.exit("Person not found.")
    
    target = person_id_for_name(input("Name: "))
    if target is None:
        logging.error("Person not found.")
        sys.exit("Person not found.")

    logging.info(f"Searching for path from {source} to {target}.")
    path = shortest_path(source, target)

    if path is None:
        logging.info("No connection found.")
        print("Not connected.")
    else:
        degrees = len(path)
        logging.info(f"{degrees} degrees of separation found.")
        print(f"{degrees} degrees of separation.")
        path = [(None, source)] + path
        for i in range(degrees):
            person1 = people[path[i][1]]["name"]
            person2 = people[path[i + 1][1]]["name"]
            movie = movies[path[i + 1][0]]["title"]
            print(f"{i + 1}: {person1} and {person2} starred in {movie}")


def shortest_path(source, target):
    """
    Returns the shortest list of (movie_id, person_id) pairs
    that connect the source to the target.

    If no possible path, returns None.
    """
    logging.info(f"Starting search from {source} to {target}")

    # Initialize frontier and explored set
    start = Node(state=source, parent=None, action=None)
    frontier = QueueFrontier()
    frontier.add(start)
    explored = set()

    while True:
        if frontier.empty():
            logging.info("No path found; frontier is empty.")
            return None  # No solution found

        node = frontier.remove()
        logging.info(f"Exploring node: {node.state}")

        # If goal is reached, reconstruct the path
        if node.state == target:
            path = []
            while node.parent is not None:
                path.append((node.action, node.state))
                node = node.parent
            path.reverse()
            logging.info(f"Path found: {path}")
            return path  # Return the found path

        # Mark the node as explored
        explored.add(node.state)

        # Add neighbors to the frontier
        for movie_id, person_id in neighbors_for_person(node.state):
            if not frontier.contains_state(person_id) and person_id not in explored:
                child = Node(state=person_id, parent=node, action=movie_id)
                frontier.add(child)
                logging.info(f"Added {person_id} to frontier via movie {movie_id}")


def person_id_for_name(name):
    """
    Returns the IMDB id for a person's name,
    resolving ambiguities as needed.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        logging.warning(f"Person {name} not found.")
        return None
    elif len(person_ids) > 1:
        logging.info(f"Ambiguity found for name {name}")
        print(f"Which '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            name = person["name"]
            birth = person["birth"]
            print(f"ID: {person_id}, Name: {name}, Birth: {birth}")
        try:
            person_id = input("Intended Person ID: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


def neighbors_for_person(person_id):
    """
    Returns (movie_id, person_id) pairs for people
    who starred with a given person.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for person_id in movies[movie_id]["stars"]:
            neighbors.add((movie_id, person_id))
    return neighbors


if __name__ == "__main__":
    main()
