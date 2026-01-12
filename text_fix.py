# Code from eruvanos https://github.com/pythonarcade/arcade/pull/2459

import pyglet

class ArcadeTextLayoutGroup(pyglet.text.layout.TextLayoutGroup):
    """Create a text layout rendering group.
    Overrides pyglet blending handling to allow for additive blending.
    Furthermore, it resets the blend function to the previous state.
    """

    _prev_blend = None
    _prev_blend_func = None

    def set_state(self) -> None:
        import pyglet.gl as gl
        from ctypes import c_int, c_ubyte

        self.program.use()
        self.program["scissor"] = False

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(self.texture.target, self.texture.id)

        blend = c_ubyte()
        gl.glGetBooleanv(gl.GL_BLEND, blend)
        self._prev_blend = bool(blend.value)

        src_rgb = c_int()
        dst_rgb = c_int()
        src_alpha = c_int()
        dst_alpha = c_int()
        gl.glGetIntegerv(gl.GL_BLEND_SRC_RGB, src_rgb)
        gl.glGetIntegerv(gl.GL_BLEND_DST_RGB, dst_rgb)
        gl.glGetIntegerv(gl.GL_BLEND_SRC_ALPHA, src_alpha)
        gl.glGetIntegerv(gl.GL_BLEND_DST_ALPHA, dst_alpha)

        self._prev_blend_func = (src_rgb.value, dst_rgb.value,
            src_alpha.value, dst_alpha.value)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(
            gl.GL_SRC_ALPHA,
            gl.GL_ONE_MINUS_SRC_ALPHA,
            gl.GL_ONE,
            gl.GL_ONE,
        )

    def unset_state(self) -> None:
        import pyglet.gl as gl

        if not self._prev_blend:
            gl.glDisable(gl.GL_BLEND)

        gl.glBlendFuncSeparate(
            self._prev_blend_func[0],
            self._prev_blend_func[1],
            self._prev_blend_func[2],
            self._prev_blend_func[3],
        )
        self.program.stop()
