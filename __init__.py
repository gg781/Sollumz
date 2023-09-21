# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from . import auto_load
from . import sollumz_debug


bl_info = {
    "name": "Sollumz",
    "author": "Skylumz and Colton",
    "description": "This plugins allows you to import/export codewalker xml files.",
    "blender": (3, 5, 1),
    "version": (2, 1, 0),
    "category": "Import-Export"
}


sollumz_debug.init_debug()  # first in case we need to debug initialization code
auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
