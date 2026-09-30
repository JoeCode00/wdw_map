from pathlib import Path
import cv2
import numpy as np
from typing import cast
from src.screenshot import save_image

class vector2(np.ndarray):
    def __new__(cls, value=(0.0, 0.0), dtype=None):
        array = np.asarray(value, dtype=dtype)
        if array.shape != (2,):
            raise ValueError(f'vector2 requires exactly two values, got shape {array.shape}')
        return array.view(cls)

    @property
    def x(self) -> float:
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self) -> float:
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

#349 arrows left-right
#400 arrows up-down
class Map():
    def __setattr__(self, name, value):
        if isinstance(self.__dict__.get(name), vector2) and not isinstance(value, vector2):
            value = vector2(value)
        super().__setattr__(name, value)

    def __init__(self, data=None, **kwargs):
        self.current_map:np.ndarray = np.zeros((0, 0, 4))
        self.correlation_map:np.ndarray = np.zeros((0, 0, 4))
        self.correlation_map_location:vector2 = vector2([0.0, 0.0])
        self.current_location:vector2 = vector2([0.0, 0.0])

        
        self.correlate_size:vector2 = vector2([2000, 2000]) #X Y

    def get_x(self, point:np.ndarray) -> float:
        return point[0]
    def get_y(self, point:np.ndarray) -> float:
        return point[1]
    def direction_hint_to_vector(self, direction_hint:str) -> np.ndarray:
        match direction_hint.lower()[0]:
            case 'r': return np.array([1, 0])  #right
            case 'u': return np.array([0, 1])  #up
            case 'l': return np.array([-1, 0])  #left
            case 'd': return np.array([0, -1])  #down
            case _: raise ValueError(f'Invalid direction_hint, got {direction_hint}, expected r, right, u, up, l, left, d, or down.')
    
    
    def update_correlation_map(self) -> None:
        self.correlation_map:np.ndarray = np.zeros((self.correlate_size[1], self.correlate_size[0], 4))
        current_map_height, current_map_width = self.current_map.shape[:2]
        # Center the window on current_map's center, not its top-left corner (current_location).
        current_map_center = self.current_location + vector2([current_map_width, current_map_height]) / 2
        self.correlation_map_location = vector2(current_map_center - self.correlate_size/2)

        
        correlation_map_height, correlation_map_width = self.correlation_map.shape[:2]
    
        # Find the current_maperlap in current_map coordinates.
        current_map_x1 = int(max(0, self.correlation_map_location.x))
        current_map_y1 = int(max(0, self.correlation_map_location.y))
        current_map_x2 = int(min(current_map_width, self.correlation_map_location.x + correlation_map_width))
        current_map_y2 = int(min(current_map_height, self.correlation_map_location.y + correlation_map_height))
    
        # If the region is completely out of bounds, return the original correlation_map.
        if current_map_x1 >= current_map_x2 or current_map_y1 >= current_map_y2:
            raise ValueError('Cannot update correlation map to be empty due to being out of bounds of current map.')
    
        # Map the current_maperlap back to correlation_map coordinates.
        correlation_map_x1 = int(current_map_x1 - self.correlation_map_location.x)
        correlation_map_y1 = int(current_map_y1 - self.correlation_map_location.y)
        correlation_map_x2 = int(correlation_map_x1 + (current_map_x2 - current_map_x1))
        correlation_map_y2 = int(correlation_map_y1 + (current_map_y2 - current_map_y1))
    
        # Perform the slice and assignment
        self.correlation_map[correlation_map_y1:correlation_map_y2, 
                             correlation_map_x1:correlation_map_x2] = (
            
            self.current_map[current_map_y1:current_map_y2,
                             current_map_x1:current_map_x2])

        if np.all(self.correlation_map[..., :3] == 0):
            raise ValueError('Correlation map BGR channels are completely black.')
        if np.all(self.correlation_map[..., 3] == 0):
            raise ValueError('Correlation map alpha channel is completely transparent.')
        
    def correlate_image(self, new_image:np.ndarray) -> vector2:
        try:
            # The correlation_map is mostly unpainted (alpha==0) canvas around the real map data.
            # A plain matchTemplate scores the *whole* template against every window, so a window
            # that overlaps 100% blank-vs-blank (e.g. zero offset, template fully off the painted
            # area) is never penalized, while the true overlapping offset is penalized for the
            # sliver of template that falls outside the painted area. That biases the peak toward
            # degenerate positions. Instead, compute a masked NCC that only considers the painted
            # (valid) pixels of correlation_map at each candidate offset.
            correlation_map_gray = cv2.cvtColor(self.correlation_map.astype(np.float32), cv2.COLOR_BGRA2GRAY)
            valid_mask = (self.correlation_map[..., 3] > 0).astype(np.float32)
            image = correlation_map_gray * valid_mask

            template = cv2.cvtColor(new_image.astype(np.float32), cv2.COLOR_BGRA2GRAY)
            template_height, template_width = template.shape
            ones = np.ones_like(template)

            # Box sums over each candidate window, restricted to painted correlation_map pixels.
            valid_count = cv2.matchTemplate(valid_mask, ones, cv2.TM_CCORR)
            sum_image = cv2.matchTemplate(image, ones, cv2.TM_CCORR)
            sum_image_sq = cv2.matchTemplate(image * image, ones, cv2.TM_CCORR)
            sum_template_masked = cv2.matchTemplate(valid_mask, template, cv2.TM_CCORR)
            sum_template_sq_masked = cv2.matchTemplate(valid_mask, template * template, cv2.TM_CCORR)
            sum_cross_masked = cv2.matchTemplate(image, template, cv2.TM_CCORR)

            with np.errstate(divide='ignore', invalid='ignore'):
                mean_image = sum_image / valid_count
                mean_template = sum_template_masked / valid_count
                numerator = sum_cross_masked - valid_count * mean_image * mean_template
                image_variance = sum_image_sq - valid_count * mean_image ** 2
                template_variance = sum_template_sq_masked - valid_count * mean_template ** 2
                denominator = np.sqrt(np.clip(image_variance, 0, None) * np.clip(template_variance, 0, None))
                signal_map = np.divide(numerator, denominator, out=np.full_like(numerator, -1.0), where=denominator > 1e-6)

            # Require enough painted overlap for a candidate offset to be trustworthy.
            min_valid_pixels = 0.2 * template_height * template_width
            signal_map[valid_count < min_valid_pixels] = -1.0

            _, signal, _, location = cv2.minMaxLoc(signal_map)
            print(f'signal: {np.round(signal, 3)}')
            float_point_image_loc_in_correlated_space = vector2(location)
            # correlation_map_location already accounts for current_location; don't add it twice.
            image_location = vector2(self.correlation_map_location + float_point_image_loc_in_correlated_space)
            return image_location
        except Exception as e:
            print(f'Unable to correlate image with correlation_map at {self.correlation_map_location}.')
            raise e

    def update_current_map(self, new_image:np.ndarray, image_location:vector2=vector2([0, 0]), first_image:bool=False) -> None:
        if first_image: #set current_map as the image
            self.current_map = new_image
            self.current_location = vector2([0.0, 0.0])

        image_height, image_width = new_image.shape[:2]
        current_map_height, current_map_width = self.current_map.shape[:2]
        if new_image.ndim != 3 or new_image.shape[2] != 4:
            raise ValueError('new_image must have four BGRA channels.')

        min_x = int(np.floor(min(0.0, image_location.x)))
        min_y = int(np.floor(min(0.0, image_location.y)))
        max_x = int(np.ceil(max(current_map_width, image_location.x + image_width)))
        max_y = int(np.ceil(max(current_map_height, image_location.y + image_height)))
        canvas_width = max_x - min_x
        canvas_height = max_y - min_y
        offset_x = -min_x
        offset_y = -min_y

        destination = np.zeros((canvas_height, canvas_width, 4), dtype=np.float32)
        if current_map_height and current_map_width:
            destination[
                offset_y:offset_y + current_map_height,
                offset_x:offset_x + current_map_width,
            ] = self.current_map.astype(np.float32)

        source = new_image.astype(np.float32)
        source_alpha = np.clip(source[..., 3:4] / 255.0, 0.0, 1.0)
        source[..., :3] *= source_alpha
        source[..., 3:4] = source_alpha * 255.0

        transform = np.array(
            [[1.0, 0.0, image_location.x + offset_x],
             [0.0, 1.0, image_location.y + offset_y]],
            dtype=np.float32,
        )
        warped = cv2.warpAffine(
            source,
            transform,
            (canvas_width, canvas_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

        warped_alpha = np.clip(warped[..., 3:4] / 255.0, 0.0, 1.0)
        warped[..., 3:4] = warped_alpha * 255.0
        warped[..., :3] = np.clip(warped[..., :3], 0.0, warped[..., 3:4])
        warped_premultiplied = warped[..., :3]

        destination_alpha = np.clip(destination[..., 3:4] / 255.0, 0.0, 1.0)
        destination_premultiplied = destination[..., :3] * destination_alpha
        output_alpha = warped_alpha + destination_alpha * (1.0 - warped_alpha)
        output_premultiplied = (
            warped_premultiplied
            + destination_premultiplied * (1.0 - warped_alpha)
        )
        destination[..., :3] = np.divide(
            output_premultiplied,
            output_alpha,
            out=np.zeros_like(output_premultiplied),
            where=output_alpha > 0.0,
        )
        destination[..., 3:4] = output_alpha * 255.0

        self.current_map = destination
        self.current_location = vector2(self.current_location + vector2([offset_x, offset_y]))



    def add_image(self, new_image_path:Path, direction_hint:str, first_image:bool=False):
        new_image = cv2.imread(new_image_path, cv2.IMREAD_UNCHANGED)  #height x width x BGR
        if new_image is not None and new_image.ndim == 3 and new_image.shape[2] == 3:
            new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2BGRA) #height x width x BGRA
        new_image = cast(np.ndarray, new_image)
        if first_image:
            self.update_current_map(new_image=new_image, first_image=first_image)
        else:
            self.update_correlation_map()
            save_image(image=self.correlation_map, filename='correlation_map.png')
            image_location = self.correlate_image(new_image)
            print(image_location)
            #todo integrate direction_hint to verify image location validity
            self.update_current_map(new_image=new_image, image_location=image_location)
        

if __name__ == '__main__':
    map = Map()
    map.add_image(new_image_path=Path('/home/joseph/Documents/GitHub/wdw_map/sc1.png'), direction_hint='l', first_image=True)
    map.add_image(new_image_path=Path('/home/joseph/Documents/GitHub/wdw_map/sc2.png'), direction_hint='r')
    map.add_image(new_image_path=Path('/home/joseph/Documents/GitHub/wdw_map/sc3.png'), direction_hint='u')
    map.add_image(new_image_path=Path('/home/joseph/Documents/GitHub/wdw_map/sc4.png'), direction_hint='l')

    
    save_image(image=map.current_map, filename='composite.png')
    