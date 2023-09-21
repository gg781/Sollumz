import xml.etree.ElementTree as ET
import os
from .element import (
    ElementTree,
    ElementProperty,
    ListProperty,
    TextProperty,
)
from .drawable import ParametersList, VertexLayoutList
from ..tools import jenkhash
from typing import Optional


class RenderBucketProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or "RenderBucket", value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        items = element.text.strip().split(" ")
        for item in items:
            new.value.append(int(item))
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = " ".join(self.value)


class FileNameList(ListProperty):
    class FileName(TextProperty):
        tag_name = "Item"

    list_type = FileName
    tag_name = "FileName"


class LayoutList(ListProperty):
    class Layout(VertexLayoutList):
        tag_name = "Item"

    list_type = Layout
    tag_name = "Layout"


class Shader(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.filename = TextProperty("Name", "")
        self.render_buckets = RenderBucketProperty()
        self.layouts = LayoutList()
        self.parameters = ParametersList("Parameters")

    @property
    def required_tangent(self):
        for layout in self.layouts:
            if "Tangent" in layout.value:
                return True
        return False

    @property
    def used_texcoords(self) -> set[str]:
        names = set()
        for layout in self.layouts:
            for field_name in layout.value:
                if "TexCoord" in field_name:
                    names.add(field_name)

        return names

    @property
    def is_uv_animation_supported(self) -> bool:
        has_uv0 = False
        has_uv1 = False
        for param in self.parameters:
            if param.name == "globalAnimUV0":
                has_uv0 = True
            if param.name == "globalAnimUV1":
                has_uv1 = True

        return has_uv0 and has_uv1


class ShaderManager:
    shaderxml = os.path.join(os.path.dirname(__file__), "Shaders.xml")
    # Map shader filenames to base shader names
    _shaders_base_names: dict[Shader, str] = {}
    _shaders: dict[str, Shader] = {}
    _shaders_by_hash: dict[int, Shader] = {}

    terrains = ["terrain_cb_w_4lyr.sps", "terrain_cb_w_4lyr_lod.sps", "terrain_cb_w_4lyr_spec.sps", "terrain_cb_w_4lyr_spec_pxm.sps", "terrain_cb_w_4lyr_pxm_spm.sps",
                "terrain_cb_w_4lyr_pxm.sps", "terrain_cb_w_4lyr_cm_pxm.sps", "terrain_cb_w_4lyr_cm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm.sps",
                "terrain_cb_w_4lyr_2tex.sps", "terrain_cb_w_4lyr_2tex_blend.sps", "terrain_cb_w_4lyr_2tex_blend_lod.sps", "terrain_cb_w_4lyr_2tex_blend_pxm.sps",
                "terrain_cb_w_4lyr_2tex_blend_pxm_spm.sps", "terrain_cb_w_4lyr_2tex_pxm.sps", "terrain_cb_4lyr.sps", "terrain_cb_w_4lyr_spec_int_pxm.sps",
                "terrain_cb_w_4lyr_spec_int.sps", "terrain_cb_4lyr_lod.sps"]
    mask_only_terrains = ["terrain_cb_w_4lyr_cm.sps", "terrain_cb_w_4lyr_cm_tnt.sps",
                          "terrain_cb_w_4lyr_cm_pxm_tnt.sps", "terrain_cb_w_4lyr_cm_pxm.sps"]
    cutouts = ["cutout.sps", "cutout_um.sps", "cutout_tnt.sps", "cutout_fence.sps", "cutout_fence_normal.sps", "cutout_hard.sps", "cutout_spec_tnt.sps", "normal_cutout.sps",
               "normal_cutout_tnt.sps", "normal_cutout_um.sps", "normal_spec_cutout.sps", "normal_spec_cutout_tnt.sps", "trees_lod.sps", "trees.sps", "trees_tnt.sps",
               "trees_normal.sps", "trees_normal_spec.sps", "trees_normal_spec_tnt.sps", "trees_normal_diffspec.sps", "trees_normal_diffspec_tnt.sps"]
    alphas = ["normal_spec_alpha.sps", "normal_spec_reflect_alpha.sps", "normal_spec_reflect_emissivenight_alpha.sps", "normal_spec_screendooralpha.sps", "normal_alpha.sps",
              "normal_reflect_alpha.sps", "emissive_alpha.sps", "emissive_alpha_tnt.sps", "emissive_clip.sps", "emissive_additive_alpha.sps", "emissivenight_alpha.sps", "emissivestrong_alpha.sps",
              "spec_alpha.sps", "spec_reflect_alpha.sps", "alpha.sps", "reflect_alpha.sps", "normal_screendooralpha.sps", "spec_screendooralpha.sps", "cloth_spec_alpha.sps",
              "cloth_normal_spec_alpha.sps"]
    glasses = ["glass.sps", "glass_pv.sps", "glass_pv_env.sps", "glass_env.sps", "glass_spec.sps", "glass_reflect.sps", "glass_emissive.sps", "glass_emissivenight.sps",
               "glass_emissivenight_alpha.sps", "glass_breakable.sps", "glass_breakable_screendooralpha.sps", "glass_displacement.sps", "glass_normal_spec_reflect.sps",
               "glass_emissive_alpha.sps"]
    decals = ["decal.sps", "decal_tnt.sps", "decal_glue.sps", "decal_spec_only.sps", "decal_normal_only.sps", "decal_emissive_only.sps", "decal_emissivenight_only.sps",
              "decal_amb_only.sps", "normal_decal.sps", "normal_decal_pxm.sps", "normal_decal_pxm_tnt.sps", "normal_decal_tnt.sps", "normal_spec_decal.sps", "normal_spec_decal_detail.sps",
              "normal_spec_decal_nopuddle.sps", "normal_spec_decal_tnt.sps", "normal_spec_decal_pxm.sps", "spec_decal.sps", "spec_reflect_decal.sps", "reflect_decal.sps", "decal_dirt.sps",
              "mirror_decal.sps", "grass_batch.sps"]
    veh_cutouts = ["vehicle_cutout.sps", "vehicle_badges.sps"]
    veh_glasses = ["vehicle_vehglass.sps", "vehicle_vehglass_inner.sps"]
    veh_decals = ["vehicle_decal.sps", "vehicle_decal2.sps",
                  "vehicle_blurredrotor_emissive.sps"]
    shadow_proxies = ["trees_shadow_proxy.sps"]
    tint_flag_1 = ["trees_normal_diffspec_tnt.sps",
                   "trees_tnt.sps", "trees_normal_spec_tnt.sps"]
    tint_flag_2 = ["weapon_normal_spec_detail_tnt.sps", "weapon_normal_spec_cutout_palette.sps",
                   "weapon_normal_spec_detail_palette.sps", "weapon_normal_spec_palette.sps"]
    em_shaders = ["normal_spec_emissive.sps", "normal_spec_reflect_emissivenight.sps", "emissive.sps", "emissive_speclum.sps", "emissive_tnt.sps", "emissivenight.sps",
                  "emissivenight_geomnightonly.sps", "emissivestrong_alpha.sps", "emissivestrong.sps", "glass_emissive.sps", "glass_emissivenight.sps", "glass_emissivenight_alpha.sps",
                  "glass_emissive_alpha.sps", "decal_emissive_only.sps", "decal_emissivenight_only.sps"]
    water_shaders = ["water_fountain.sps",
                     "water_poolenv.sps", "water_decal.sps", "water_terrainfoam.sps", "water_riverlod.sps", "water_shallow.sps", "water_riverfoam.sps", "water_riverocean.sps", "water_rivershallow.sps"]

    def tinted_shaders():
        return ShaderManager.cutouts + ShaderManager.alphas + ShaderManager.glasses + ShaderManager.decals + ShaderManager.veh_cutouts + ShaderManager.veh_glasses + ShaderManager.veh_decals + ShaderManager.shadow_proxies

    def cutout_shaders():
        return ShaderManager.cutouts + ShaderManager.veh_cutouts + ShaderManager.shadow_proxies

    @staticmethod
    def load_shaders():
        tree = ET.parse(ShaderManager.shaderxml)

        for node in tree.getroot():
            base_name = node.find("Name").text
            for filename_elem in node.findall("./FileName//*"):
                filename = filename_elem.text

                if filename is None:
                    continue

                filename_hash = jenkhash.Generate(filename)

                shader = Shader.from_xml(node)
                shader.filename = filename
                ShaderManager._shaders[filename] = shader
                ShaderManager._shaders_by_hash[filename_hash] = shader
                ShaderManager._shaders_base_names[shader] = base_name

    @staticmethod
    def find_shader(filename: str) -> Optional[Shader]:
        shader = ShaderManager._shaders.get(filename, None)
        if shader is None and filename.startswith("hash_"):
            filename_hash = int(filename[5:], 16)
            shader = ShaderManager._shaders_by_hash.get(filename_hash, None)
        return shader

    @staticmethod
    def find_shader_base_name(filename: str) -> Optional[str]:
        shader = ShaderManager.find_shader(filename)
        if shader is None:
            return None
        return ShaderManager._shaders_base_names[shader]

ShaderManager.load_shaders()
