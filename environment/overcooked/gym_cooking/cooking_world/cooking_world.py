from collections import defaultdict
from gym_cooking.cooking_world.world_objects import *

from pathlib import Path
import os.path
import json
import random

# HARDCODE MIXABLE INGREDS
MIXABLE_INGREDS = {'Lettuce':['Tomato', 'Carrot', 'Onion', 'Potato', 'Broccoli'],
                   'Tomato': ['Lettuce','Carrot', 'Onion', 'Potato', 'Broccoli'],
                   'Onion':['Carrot', 'Lettuce', 'Tomato', 'Potato', 'Broccoli'],
                   'Carrot':['Tomato', 'Onion', 'Lettuce', 'Potato', 'Broccoli'],
                   'Potato': ['Lettuce', 'Tomato', 'Onion', 'Carrot', 'Broccoli'],
                   'Broccoli': ['Tomato', 'Onion', 'Lettuce', 'Carrot', 'Potato']}

def is_mixable(food, container):
    if len(container.content)==0:
        return True
    contained_food = [type(f).__name__ for f in container.content]
    food_name = type(food).__name__
    if food_name in contained_food:
        # do not accept the same ingred
        return False
    if all([food_name in MIXABLE_INGREDS[type(food_obj).__name__] for food_obj in container.content]):
        return True
    return False
    


class CookingWorld:

    COLORS = ['blue', 'magenta', 'yellow', 'green']

    SymbolToClass = {
        ' ': Floor,
        '-': Counter,
        '/': CutBoard,
        '*': DeliverSquare,
        't': Tomato,
        'l': Lettuce,
        'o': Onion,
        'p': Plate,
        'b': Blender
    }

    # AGENT_ACTIONS: 0: Noop, 1: Left, 2: right, 3: down, 4: up, 5: interact

    def __init__(self):
        self.agents = []
        self.width = 0
        self.height = 0
        self.world_objects = defaultdict(list)
        self.abstract_index = defaultdict(list)

    def add_object(self, obj):
        self.world_objects[type(obj).__name__].append(obj)

    def delete_object(self, obj):
        self.world_objects[type(obj).__name__].remove(obj)

    def index_objects(self):
        for type_name, obj_list in self.world_objects.items():
            for abstract_class in ABSTRACT_GAME_CLASSES:
                if issubclass(StringToClass[type_name], abstract_class):
                    self.abstract_index[abstract_class].extend(obj_list)

    def get_object_list(self):
        object_list = []
        for value in self.world_objects.values():
            object_list.extend(value)
        return object_list

    def progress_world(self):
        for obj in self.abstract_index[ProgressingObject]:
            dynamic_objects = self.get_objects_at(obj.location, DynamicObject)
            obj.progress(dynamic_objects)

    def perform_agent_actions(self, agents, actions):
        for agent, action in zip(agents, actions):
            if 0 < action < 5:
                agent.change_orientation(action)
        cleaned_actions = self.check_inbounds(agents, actions)
        collision_actions = self.check_collisions(agents, cleaned_actions)
        for agent, action in zip(agents, collision_actions):
            self.perform_agent_action(agent, action)
        self.progress_world()

    def perform_agent_action(self, agent: Agent, action):
        if 0 < action < 5:
            self.resolve_walking_action(agent, action)
        if action == 5:
            interaction_location = self.get_target_location(agent, agent.orientation)
            if any([agent.location == interaction_location for agent in self.agents]):
                return
            dynamic_objects = self.get_objects_at(interaction_location, DynamicObject)
            static_object = self.get_objects_at(interaction_location, StaticObject)[0]
            if not agent.holding and not dynamic_objects:
                return
            elif agent.holding and not dynamic_objects:
                if static_object.accepts([agent.holding]):
                    agent.put_down(interaction_location)
            elif not agent.holding and dynamic_objects:
                object_to_grab = self.get_highest_order_object(dynamic_objects)
                if isinstance(static_object, ActionObject):
                    action_done = static_object.action(dynamic_objects)
                    if not action_done:
                        agent.grab(object_to_grab)
                else:
                    agent.grab(object_to_grab)
            elif agent.holding and dynamic_objects:
                self.attempt_merge(agent, dynamic_objects, interaction_location)

    def resolve_walking_action(self, agent: Agent, action):
        target_location = self.get_target_location(agent, action)
        if self.square_walkable(target_location):
            agent.move_to(target_location)

    def get_highest_order_object(self, objects: List[DynamicObject]):
        order = [Container, Food]
        for obj_type in order:
            obj = self.filter_obj(objects, obj_type)
            if obj:
                return obj
        return None

    @staticmethod
    def get_target_location(agent, action):
        if action == 1:
            target_location = (agent.location[0] - 1, agent.location[1])
        elif action == 2:
            target_location = (agent.location[0] + 1, agent.location[1])
        elif action == 3:
            target_location = (agent.location[0], agent.location[1] + 1)
        elif action == 4:
            target_location = (agent.location[0], agent.location[1] - 1)
        else:
            target_location = (agent.location[0], agent.location[1])
        return target_location

    @staticmethod
    def filter_obj(objects: List[DynamicObject], obj_type):
        filtered_objects = [obj for obj in objects if isinstance(obj, obj_type)]
        if len(filtered_objects) > 1:
            raise Exception(f"Too many {obj_type} in one place!")
        elif len(filtered_objects) == 1:
            return filtered_objects[0]
        else:
            return None

    def check_inbounds(self, agents, actions):
        cleaned_actions = []
        for agent, action in zip(agents, actions):
            if action == 0 or action == 5:
                cleaned_actions.append(action)
                continue
            target_location = self.get_target_location(agent, action)
            if target_location[0] > self.width - 1 or target_location[0] < 0:
                action = 0
            if target_location[1] > self.height - 1 or target_location[1] < 0:
                action = 0
            cleaned_actions.append(action)
        return cleaned_actions

    def check_collisions(self, agents, actions):
        collision_actions = []
        target_locations = []
        walkable = []
        current_pos = [agent.location for agent in agents]
        for agent, action in zip(agents, actions):
            target_location = self.get_target_location(agent, action)
            target_walkable = self.square_walkable(target_location)
            end_location = target_location if target_walkable else agent.location
            target_locations.append(end_location)
            walkable.append(target_walkable)
        for idx, (action, target_location, target_walkable) in enumerate(zip(actions, target_locations, walkable)):
            # if target_location in target_locations[:idx] + target_locations[idx+1:] and target_walkable:
            if action !=5 and target_location in target_locations[:idx] + current_pos[:idx] + current_pos[idx+1:] and target_walkable:
                collision_actions.append(0)
            else:
                collision_actions.append(action)
        return collision_actions

    def square_walkable(self, location):
        objects = self.get_objects_at(location, StaticObject)
        if len(objects) != 1:
            raise Exception(f"Not exactly one static object at location: {location}")
        return objects[0].walkable

    def get_abstract_object_at(self, location, object_type):
        return [obj for obj in self.abstract_index[object_type] if obj.location == location]

    def get_objects_at(self, location, object_type=object):
        located_objects = []
        for obj_class_string, objects in self.world_objects.items():
            obj_class = StringToClass[obj_class_string]
            if not issubclass(obj_class, object_type):
                continue
            for obj in objects:
                if obj.location == location:
                    located_objects.append(obj)
        return located_objects

    def attempt_merge(self, agent: Agent, dynamic_objects: List[DynamicObject], target_location):
        highest_order_obj = self.get_highest_order_object(dynamic_objects)
        if isinstance(highest_order_obj, Container) and isinstance(agent.holding, Food):
            if agent.holding.done():
                if is_mixable(agent.holding, highest_order_obj):
                    highest_order_obj.add_content(agent.holding)
                    agent.put_down(target_location)
        if isinstance(highest_order_obj, Food) and isinstance(agent.holding, Container):
            if highest_order_obj.done():
                if is_mixable(highest_order_obj, agent.holding):
                    agent.holding.add_content(highest_order_obj)
                    highest_order_obj.move_to(agent.location)

    def load_new_style_level(self, level_name, num_agents):
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        parent = path.parent / f"utils/new_style_level/{level_name}.json"
        with open(parent) as json_file:
            level_object = json.load(json_file)
            json_file.close()
        self.parse_level_layout(level_object)
        self.parse_static_objects(level_object)
        self.parse_dynamic_objects(level_object)
        self.parse_agents(level_object, num_agents)

    def parse_level_layout(self, level_object):
        level_layout = level_object["LEVEL_LAYOUT"]
        x = 0
        y = 0
        for y, line in enumerate(iter(level_layout.splitlines())):
            for x, char in enumerate(line):
                if char == "-":
                    counter = Counter(location=(x, y))
                    self.add_object(counter)
                else:
                    floor = Floor(location=(x, y))
                    self.add_object(floor)
        self.width = x + 1
        self.height = y + 1

    def parse_static_objects(self, level_object):
        static_objects = level_object["STATIC_OBJECTS"]
        for static_object in static_objects:
            name = list(static_object.keys())[0]
            for idx in range(static_object[name]["COUNT"]):
                time_out = 0
                while True:
                    x = random.sample(static_object[name]["X_POSITION"], 1)[0]
                    y = random.sample(static_object[name]["Y_POSITION"], 1)[0]
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), StaticObject)

                    counter = [obj for obj in static_objects_loc if isinstance(obj, (Counter, Floor))]
                    if counter:
                        if len(counter) != 1:
                            raise ValueError("Too many counter in one place detected during initialization")
                        self.delete_object(counter[0])
                        obj = StringToClass[name](location=(x, y))
                        self.add_object(obj)
                        break
                    else:
                        time_out += 1
                        if time_out > 100:
                            raise ValueError(f"Can't find valid position for object: "
                                             f"{static_object} in {time_out} steps")
                        continue

    def parse_dynamic_objects(self, level_object):
        dynamic_objects = level_object["DYNAMIC_OBJECTS"]
        for dynamic_object in dynamic_objects:
            name = list(dynamic_object.keys())[0]
            for idx in range(dynamic_object[name]["COUNT"]):
                time_out = 0
                while True:
                    x = random.sample(dynamic_object[name]["X_POSITION"], 1)[0]
                    y = random.sample(dynamic_object[name]["Y_POSITION"], 1)[0]
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), Counter)
                    dynamic_objects_loc = self.get_objects_at((x, y), DynamicObject)

                    if len(static_objects_loc) == 1 and not dynamic_objects_loc:
                        obj = StringToClass[name](location=(x, y))
                        self.add_object(obj)
                        break
                    else:
                        time_out += 1
                        if time_out > 100:
                            raise ValueError(f"Can't find valid position for object: "
                                             f"{dynamic_object} in {time_out} steps")
                        continue

    def parse_agents(self, level_object, num_agents):
        agent_objects = level_object["AGENTS"]
        agent_idx = 0
        for agent_object in agent_objects:
            for idx in range(agent_object["MAX_COUNT"]):
                agent_idx += 1
                if agent_idx > num_agents:
                    return
                time_out = 0
                while True:
                    x = random.sample(agent_object["X_POSITION"], 1)[0]
                    y = random.sample(agent_object["Y_POSITION"], 1)[0]
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of agent is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), Floor)
                    if not any([(x, y) == agent.location for agent in self.agents]) and static_objects_loc:
                        agent = Agent((int(x), int(y)), self.COLORS[len(self.agents)],
                                      'agent-' + str(len(self.agents) + 1))
                        self.agents.append(agent)
                        break
                    else:
                        time_out += 1
                        if time_out > 100:
                            raise ValueError(f"Can't find valid position for agent: {agent_object} in {time_out} steps")

    def load_level(self, level, num_agents):
        self.load_new_style_level(level, num_agents)
        self.index_objects()
