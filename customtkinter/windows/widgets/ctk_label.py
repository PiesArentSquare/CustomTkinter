import tkinter
from typing import Union, Tuple, Callable

from .core_rendering.ctk_canvas import CTkCanvas
from .theme.theme_manager import ThemeManager
from .core_rendering.draw_engine import DrawEngine
from .core_widget_classes.widget_base_class import CTkBaseClass
from .font.ctk_font import CTkFont
from .image.ctk_image import CTkImage

from customtkinter.utility.utility_functions import pop_from_dict_by_set, check_kwargs_empty


class CTkLabel(CTkBaseClass):
    """
    Label with rounded corners. Default is fg_color=None (transparent fg_color).
    For detailed information check out the documentation.
    """

    # attributes that are passed to and managed by the tkinter entry only:
    _valid_tk_label_attributes = {"cursor", "justify", "padx", "pady",
                                  "textvariable", "state", "takefocus", "underline", "wraplength"}

    def __init__(self,
                 master: any = None,
                 width: int = 0,
                 height: int = 28,
                 corner_radius: Union[int, str] = "default_theme",

                 bg_color: Union[str, Tuple[str, str], None] = None,
                 fg_color: Union[str, Tuple[str, str], None] = "default_theme",
                 text_color: Union[str, Tuple[str, str]] = "default_theme",

                 text: str = "CTkLabel",
                 font: Union[tuple, CTkFont] = "default_theme",
                 image: Union[tkinter.PhotoImage, CTkImage] = None,
                 compound: str = "center",
                 anchor: str = "center",  # label anchor: center, n, e, s, w
                 **kwargs):

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # color
        self._fg_color = ThemeManager.theme["color"]["label"] if fg_color == "default_theme" else fg_color
        self._text_color = ThemeManager.theme["color"]["text"] if text_color == "default_theme" else text_color

        # shape
        self._corner_radius = ThemeManager.theme["shape"]["label_corner_radius"] if corner_radius == "default_theme" else corner_radius

        # text
        self._anchor = anchor
        self._text = text

        # image
        self._image = self._check_image_type(image)
        self._compound = compound
        if isinstance(self._image, CTkImage):
            self._image.add_configure_callback(self._update_image)

        # font
        self._font = CTkFont() if font == "default_theme" else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._label = tkinter.Label(master=self,
                                    highlightthickness=0,
                                    padx=0,
                                    pady=0,
                                    borderwidth=0,
                                    anchor=self._anchor,
                                    compound=self._compound,
                                    text=self._text,
                                    font=self._apply_font_scaling(self._font))
        self._label.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes))

        check_kwargs_empty(kwargs, raise_error=True)

        self._create_grid()
        self._update_image()
        self._draw()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width), height=self._apply_widget_scaling(self._desired_height))
        self._label.configure(font=self._apply_font_scaling(self._font))

        self._create_grid()
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid()
        self._draw()

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nswe")

    def _update_image(self):
        if isinstance(self._image, CTkImage):
            self._label.configure(image=self._image.create_scaled_photo_image(self._get_widget_scaling(),
                                                                              self._get_appearance_mode()))
        elif self._image is not None:
            self._label.configure(image=self._image)

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _create_grid(self):
        """ configure grid system (1x1) """

        text_label_grid_sticky = self._anchor if self._anchor != "center" else ""
        self._label.grid(row=0, column=0, sticky=text_label_grid_sticky,
                         padx=self._apply_widget_scaling(min(self._corner_radius, round(self._current_height / 2))))

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              0)

        if no_color_updates is False or requires_recoloring:
            if self._apply_appearance_mode(self._fg_color) is not None:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._fg_color),
                                        outline=self._apply_appearance_mode(self._fg_color))

                self._label.configure(fg=self._apply_appearance_mode(self._text_color),
                                      bg=self._apply_appearance_mode(self._fg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._bg_color),
                                        outline=self._apply_appearance_mode(self._bg_color))

                self._label.configure(fg=self._apply_appearance_mode(self._text_color),
                                      bg=self._apply_appearance_mode(self._bg_color))

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        if self._image is not None:
            self._update_image()

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._label.configure(text=self._text)

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "image" in kwargs:
            if isinstance(self._image, CTkImage):
                self._image.remove_configure_callback(self._update_image)
            self._image = self._check_image_type(kwargs.pop("image"))
            if isinstance(self._image, CTkImage):
                self._image.add_configure_callback(self._update_image)
            self._update_image()

        if "compound" in kwargs:
            self._compound = kwargs.pop("compound")
            self._label.configure(compound=self._compound)

        if "anchor" in kwargs:
            self._anchor = kwargs.pop("anchor")
            self._label.configure(anchor=self._anchor)
            self._create_grid()

        self._label.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes))  # configure tkinter.Label
        super().configure(require_redraw=require_redraw, **kwargs)  # configure CTkBaseClass

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "image":
            return self._image
        elif attribute_name == "compound":
            return self._compound
        elif attribute_name == "anchor":
            return self._anchor

        elif attribute_name in self._valid_tk_label_attributes:
            return self._label.cget(attribute_name)  # cget of tkinter.Label
        else:
            return super().cget(attribute_name)  # cget of CTkBaseClass

    def bind(self, sequence: str = None, command: Callable = None, add: str = None) -> str:
        """ called on the tkinter.Label and tkinter.Canvas """
        canvas_bind_return = self._canvas.bind(sequence, command, add)
        label_bind_return = self._label.bind(sequence, command, add)
        return canvas_bind_return + " + " + label_bind_return

    def unbind(self, sequence: str, funcid: str = None):
        """ called on the tkinter.Label and tkinter.Canvas """
        canvas_bind_return, label_bind_return = funcid.split(" + ")
        self._canvas.unbind(sequence, canvas_bind_return)
        self._label.unbind(sequence, label_bind_return)

    def focus(self):
        return self._label.focus()

    def focus_set(self):
        return self._label.focus_set()

    def focus_force(self):
        return self._label.focus_force()
