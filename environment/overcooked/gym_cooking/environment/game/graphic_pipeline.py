import pygame
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.misc.game.utils import *
from collections import defaultdict, namedtuple

import numpy as np
import pathlib
import os.path
import math


COLORS = ['blue', 'magenta', 'yellow', 'green']

_image_library = {}


def get_image(path):
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


GraphicsProperties = namedtuple("GraphicsProperties", ["pixel_per_tile", "holding_scale", "container_scale",
                                                       "width_pixel", "height_pixel", "tile_size", "holding_size",
                                                       "container_size", "holding_container_size"])


class GraphicPipeline:

    PIXEL_PER_TILE = 100
    HOLDING_SCALE = 0.5
    CONTAINER_SCALE = 0.7

    def __init__(self, env, display=False):
        self.env = env
        self.display = display
        self.screen = None
        self.graphics_dir = 'misc/game/graphics'
        self.graphics_properties = GraphicsProperties(self.PIXEL_PER_TILE, self.HOLDING_SCALE, self.CONTAINER_SCALE,
                                                      self.PIXEL_PER_TILE * self.env.unwrapped.world.width,
                                                      self.PIXEL_PER_TILE * self.env.unwrapped.world.height,
                                                      (self.PIXEL_PER_TILE, self.PIXEL_PER_TILE),
                                                      (self.PIXEL_PER_TILE * self.HOLDING_SCALE,
                                                       self.PIXEL_PER_TILE * self.HOLDING_SCALE),
                                                      (self.PIXEL_PER_TILE * self.CONTAINER_SCALE,
                                                       self.PIXEL_PER_TILE * self.CONTAINER_SCALE),
                                                      (self.PIXEL_PER_TILE * self.CONTAINER_SCALE * self.HOLDING_SCALE,
                                                       self.PIXEL_PER_TILE * self.CONTAINER_SCALE * self.HOLDING_SCALE))
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = pathlib.Path(dir_name)
        self.root_dir = path.parent.parent
        self.loaded_img = dict()

    def on_init(self):
        if self.display:
            self.screen = pygame.display.set_mode((self.graphics_properties.width_pixel,
                                                   self.graphics_properties.height_pixel))
        else:
            # Create a hidden surface
            self.screen = pygame.Surface((self.graphics_properties.width_pixel, self.graphics_properties.height_pixel))
        self.screen = self.screen
        return True

    def on_render(self, mode=''):
        self.screen.fill(Color.FLOOR)

        self.draw_static_objects()

        self.draw_agents()

        self.draw_dynamic_objects()

        if self.env.unwrapped.obs_range is not None:
            # print('Line drawn at', self.env.unwrapped.obs_range)
            # line_width = 10
            # surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            # pygame.draw.line(surface, Color.AERO_BLUE,
            #                  self.scaled_location([0, self.env.unwrapped.obs_range + 1]),
            #                  self.scaled_location([self.env.unwrapped.world.width, self.env.unwrapped.obs_range + 1]),
            #                  line_width)
            # self.screen.blit(surface, (0, 0))
            surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            if self.env.unwrapped.world.agents[0].location[1] > self.env.unwrapped.obs_range:
                pygame.draw.rect(surface, Color.DARK_GREY,
                                 self.scaled_location([0, 0])
                                 + self.scaled_location([self.env.unwrapped.world.width, self.env.unwrapped.obs_range + 1]))
            else:
                pygame.draw.rect(surface, Color.DARK_GREY,
                                 self.scaled_location([0, self.env.unwrapped.obs_range + 1])
                                 + self.scaled_location([self.env.unwrapped.world.width, self.env.unwrapped.world.height]))
            self.screen.blit(surface, (0, 0))

        if self.display:
            pygame.display.flip()
            pygame.display.update()
        if mode=='rgb_array':
            return self.get_image_obs()

    def draw_square(self):
        pass

    def draw_static_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        static_objects = [obj for obj in objects if isinstance(obj, StaticObject)]
        for static_object in static_objects:
            self.draw_static_object(static_object)

    def draw_static_object(self, static_object: StaticObject):
        sl = self.scaled_location(static_object.location)
        fill = pygame.Rect(sl[0], sl[1], self.graphics_properties.pixel_per_tile,
                           self.graphics_properties.pixel_per_tile)
        if isinstance(static_object, Counter):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
        elif isinstance(static_object, DeliverSquare):
            pygame.draw.rect(self.screen, Color.DELIVERY, fill)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        elif isinstance(static_object, CutBoard):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        elif isinstance(static_object, Blender):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        # elif isinstance(static_object, Floor):
        #     pygame.draw.rect(self.screen, Color.FLOOR, fill)

    def draw_dynamic_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        dynamic_objects = [obj for obj in objects if isinstance(obj, DynamicObject)]
        dynamic_objects_grouped = defaultdict(list)
        for obj in dynamic_objects:
            dynamic_objects_grouped[obj.location].append(obj)
        for location, obj_list in dynamic_objects_grouped.items():
            if any([agent.location == location for agent in self.env.unwrapped.world.agents]):
                self.draw_dynamic_object_stack(obj_list, self.graphics_properties.holding_size,
                                               self.holding_location(location),
                                               self.graphics_properties.holding_container_size,
                                               self.holding_container_location(location))
            else:
                self.draw_dynamic_object_stack(obj_list, self.graphics_properties.tile_size,
                                               self.scaled_location(location),
                                               self.graphics_properties.container_size,
                                               self.container_location(location))

    def draw_dynamic_object_stack(self, dynamic_objects, base_size, base_location, holding_size, holding_location):
        highest_order_object = self.env.unwrapped.world.get_highest_order_object(dynamic_objects)
        if isinstance(highest_order_object, Container):
            self.draw(highest_order_object.file_name(), base_size, base_location)
            rest_stack = [obj for obj in dynamic_objects if obj != highest_order_object]
            if rest_stack:
                self.draw_food_stack(rest_stack, holding_size, holding_location)
        else:
            self.draw_food_stack(dynamic_objects, base_size, base_location)

    def draw_agents(self):
        for agent in self.env.unwrapped.world.agents:
            self.draw('agent-{}'.format(agent.color), self.graphics_properties.tile_size,
                      self.scaled_location(agent.location))
            if agent.orientation == 1:
                file_name = "arrow_left"
                location = self.scaled_location(agent.location)
                location = (location[0], location[1] + self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 2:
                file_name = "arrow_right"
                location = self.scaled_location(agent.location)
                location = (location[0] + 3 * self.graphics_properties.tile_size[0] // 4,
                            location[1] + self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 3:
                file_name = "arrow_down"
                location = self.scaled_location(agent.location)
                location = (location[0] + self.graphics_properties.tile_size[0] // 4,
                            location[1] + 3 * self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 4:
                file_name = "arrow_up"
                location = self.scaled_location(agent.location)
                location = (location[0] + self.graphics_properties.tile_size[0] // 4, location[1])
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            else:
                raise ValueError(f"Agent orientation invalid ({agent.orientation})")
            self.draw(file_name, size, location)

    def get_img(self, img_path, size):
        if (img_path, size) not in self.loaded_img:
            image = pygame.transform.scale(get_image(img_path), (int(size[0]), int(size[1])))
            self.loaded_img[(img_path, size)] = image
        return self.loaded_img[(img_path, size)]

    def draw(self, path, size, location):
        image_path = f'{self.root_dir}/{self.graphics_dir}/{path}.png'
        image = self.get_img(image_path, size)
        self.screen.blit(image, location)

    def draw_food_stack(self, dynamic_objects, base_size, base_loc):
        tiles = int(math.floor(math.sqrt(len(dynamic_objects) - 1)) + 1)
        size = (base_size[0] // tiles, base_size[1] // tiles)
        for idx, obj in enumerate(dynamic_objects):
            location = (base_loc[0] + size[0] * (idx % tiles), base_loc[1] + size[1] * (idx // tiles))
            self.draw(obj.file_name(), size, location)

    def scaled_location(self, loc):
        """Return top-left corner of scaled location given coordinates loc, e.g. (3, 4)"""
        return tuple(self.graphics_properties.pixel_per_tile * np.asarray(loc))

    def holding_location(self, loc):
        """Return top-left corner of location where agent holding will be drawn (bottom right corner)
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile *
                      (1 - self.HOLDING_SCALE)).astype(int))

    def container_location(self, loc):
        """Return top-left corner of location where contained (i.e. plated) object will be drawn,
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile *
                      (1 - self.CONTAINER_SCALE) / 2).astype(int))
    
    def holding_container_location(self, loc):
        """Return top-left corner of location where contained, held object will be drawn
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        factor = (1 - self.HOLDING_SCALE) + (1 - self.CONTAINER_SCALE) / 2 * self.HOLDING_SCALE
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile * factor).astype(int))

    def get_image_obs(self):
        # self.on_render()
        # mapped_img = np.array(pygame.PixelArray(self.screen), dtype=np.uint32)
        # w,h = mapped_img.shape[:2]
        # img_int = np.array(mapped_img, dtype=np.uint32).reshape(-1)
        # np_img = np.array(list(map(self.screen.unmap_rgb, img_int))).reshape(w,h,4).transpose(1,0,2)
        # return np_img[:,:,:3]
        return pygame.surfarray.array3d(self.screen).transpose(1,0,2)

        # img_rgb = np.zeros([img_int.shape[1], img_int.shape[0], 3], dtype=np.uint8)
        # for i in range(img_int.shape[0]):
        #     for j in range(img_int.shape[1]):
        #         # color = pygame.Color(img_int[i][j])
        #         color = self.screen.unmap_rgb(img_int[i][j])
        #         img_rgb[j, i, 0] = color.r
        #         img_rgb[j, i, 1] = color.g
        #         img_rgb[j, i, 2] = color.b
        # return img_rgb

    def save_image_obs(self, t):
        game_record_dir = 'misc/game/record/example/'
        self.on_render()
        pygame.image.save(self.screen, '{}/t={:03d}.png'.format(game_record_dir, t))
