init -37 python in _translator3000_gui:
    class FileSystemWrapper(SingleTone):
        __author__ = u'Vladya'

        @property
        def desktop(self):
            user_folder = store._translator3000.utils.get_userfolder(u'ignore')
            variants = path.join(user_folder, u'Desktop'), path.join(user_folder, u'\u0420\u0430\u0431\u043e\u0447\u0438\u0439 \u0441\u0442\u043e\u043b')
            for variant in variants:
                if path.isdir(variant):
                    return variant
            return user_folder

        @staticmethod
        def _unicode_path(name):
            if not isinstance(name, basestring):
                raise TypeError(self.translate(u'\u041f\u0443\u0442\u044c \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0441\u0442\u0440\u043e\u043a\u043e\u0439.'))
            return renpy.fsdecode(name)

        @staticmethod
        def _get_hash_from_filelike_object(descriptor):
            hash = hashlib.sha512()
            try:
                descriptor.seek(0)
            except Exception:
                pass
            while True:
                chunk = descriptor.read(1073741824)
                if not chunk:
                    return hash.hexdigest()
                hash.update(chunk)

        @classmethod
        def is_same_files(cls, descriptor1, descriptor2):
            _get_hash = cls._get_hash_from_filelike_object
            if _get_hash(descriptor1) == _get_hash(descriptor2):
                return True
            return False

        @staticmethod
        def get_windows_mountdrive():
            for mount in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                mount = u'{0}:\\'.format(mount)
                if path.exists(mount):
                    yield mount

        @classmethod
        def _normpath(cls, filename):
            filename = cls._unicode_path(filename)
            if not filename.strip():
                return u''
            return path.normpath(filename.replace(u'\\', u'/'))

        @classmethod
        def dirname(cls, filename, from_renpy=True):
            filename = cls._normpath(cls._unicode_path(filename))
            if not from_renpy and renpy.windows and path.ismount(filename):
                return u''
            directory = path.dirname(filename)
            if from_renpy:
                directory = directory.replace(u'\\', u'/')
            return directory

        @classmethod
        def join(cls, *parts, **kwargs):
            from_renpy = kwargs.pop(u'from_renpy', True)
            result = cls._normpath(path.join(*parts, **kwargs))
            if from_renpy:
                result = result.replace(u'\\', u'/')
            return result

        @classmethod
        def listdir(cls, directory, from_renpy=True):
            directory = cls._normpath(directory)
            result = builtins.dict(dirs=builtins.set(), files=builtins.set())
            if from_renpy:
                for filename in map(cls._normpath, renpy.list_files()):
                    parent_dir, filename = path.split(filename)
                    if parent_dir == directory:
                        result[u'files'].add(filename)
                        continue
                    while parent_dir:
                        parent_dir, _directory = path.split(parent_dir)
                        if parent_dir == directory:
                            result[u'dirs'].add(_directory)
                            break
            elif not directory.strip():
                if renpy.windows:
                    result[u'dirs'].update(cls.get_windows_mountdrive())
            else:
                try:
                    _lisddir_result = tuple(os.listdir(directory))
                except Exception:
                    pass
                else:
                    for fn in _lisddir_result:
                        filename = store._translator3000.utils.Encoding.fsdecode(fn)
                        full_filename = path.join(directory, filename)
                        if path.isfile(full_filename):
                            result[u'files'].add(filename)
                        elif path.isdir(full_filename):
                            result[u'dirs'].add(filename)
            return builtins.dict(map(lambda x: (x[0], tuple(builtins.sorted(x[1]))), result.items()))

        @classmethod
        def get_clear_filename(cls, filename, delete_ext=True):
            filename = cls._normpath(filename)
            filename = path.basename(filename)
            if delete_ext:
                filename, _ext = path.splitext(filename)
            return filename


    class GUI(SingleTone):
        __author__ = u'Vladya'
        available_languages = frozenset((u'russian', u'english', u'chuvash', u'turkish', u'vietnamese'))

        def __init__(self, translator):
            if self.initialized:
                return
            self._m1_0x3ctranslator30000x3e__show = True
            self._translator = translator
            self._fs_object = FileSystemWrapper()
            self._loader_object = GUILoader()
            self._choice_menu_object = ChoiceMenuHandler(gui_object=self)
            self._current_menu_stack = builtins.list()
            self._orig_text_screen_data = _DragObjectData(u'original_text_box')
            self._alternate_text_screen_data = _DragObjectData(u'alternate_text_box')
            self._edit_text_screen_data = _DragObjectData(u'edit_text_box')
            self._messages_screen_data = _DragObjectData(u'messages_box')
            self._menu_info_data = _DragObjectData(u'menu_info_box')
            self._color_picker = ColorPicker(gui_object=self)
            self._message_handler = MessageHandler(gui_object=self)
            self._tooltip_handler = TooltipHandler(gui_object=self)
            self._original_sample_text = u'''\u0421\u044a\u0435\u0448\u044c \u0436\u0435 \u0435\u0449\u0451 \u044d\u0442\u0438\u0445 \u043c\u044f\u0433\u043a\u0438\u0445 \u0444\u0440\u0430\u043d\u0446\u0443\u0437\u0441\u043a\u0438\u0445 \u0431\u0443\u043b\u043e\u043a, \u0434\u0430 \u0432\u044b\u043f\u0435\u0439 \u0447\u0430\u044e.
The quick brown fox jumps over the lazy dog.
(1 + 2) - 3 = (45 / 6789) * 0'''
            self._sample_text = self.translate(self._original_sample_text)
            self.initialized = True

        @property
        def loader(self):
            return self._loader_object

        @property
        def mode(self):
            if self._translator._translate_preparer._switcher:
                return u'prescan'
            elif self._translator._translator_switcher:
                if self._translator._use_database_only:
                    return u'db_only'
                return u'realtime'
            return u'off'

        @mode.setter
        def mode(self, new_mode):
            new_mode = new_mode.strip().lower()
            if new_mode == u'off':
                self._translator._translator_switcher = False
                self._translator._use_database_only = False
                self._translator._translate_preparer._switcher = False
            elif new_mode == u'db_only':
                self._translator._translator_switcher = True
                self._translator._use_database_only = True
                self._translator._translate_preparer._switcher = False
            elif new_mode == u'realtime':
                self._translator._translator_switcher = True
                self._translator._use_database_only = False
                self._translator._translate_preparer._switcher = False
            elif new_mode == u'prescan':
                self._translator._translator_switcher = False
                self._translator._use_database_only = False
                self._translator._translate_preparer._switcher = True
            else:
                raise ValueError(new_mode)
            self._translator._translator_object.interrupt_all_translations()
            if new_mode in (u'db_only', u'realtime'):
                self._translator.update_work_method()
            renpy.run(store._translator3000.Translator3000.NeedRestartAction())

        def _get_keys(self):
            return builtins.dict(self._m1_0x3ctranslator30000x3e__get_keys())

        def _m1_0x3ctranslator30000x3e__get_keys(self):
            for k, v in self._translator._setting[u'keys'].items():
                if v is None:
                    yield k, None
                    continue
                yield k, _PressedKey(data_from_setting=v)

        def _confirm(self, message, action):
            return self._forward(u'translator3000_confirm_screen', message=message, yes_action=action)

        def _back(self):
            if not renpy.context()._menu:
                self._current_menu_stack = builtins.list()
            if not self._current_menu_stack:
                renpy.run(self._tooltip_handler.DismissAction())
                return setattr(self, u'show', False)
            self._current_menu_stack.pop()
            if not self._current_menu_stack:
                return renpy.run((self._tooltip_handler.DismissAction(), store.Return()))
            _screen, _args, _kwargs = self._current_menu_stack[-1]
            return renpy.run((self._tooltip_handler.DismissAction(), store.Scroll(u'tr3000_main_vpg', u'vertical decrease', getattr(sys, u'maxint', int(10000000000.0))), store.ShowMenu(_screen, *_args, **_kwargs)))

        def _forward(self, dest_screen, *screen_args, **screen_kwargs):
            _force_clean_stack = screen_kwargs.pop(u'_force_clean_stack', False)
            if _force_clean_stack or not renpy.context()._menu:
                self._current_menu_stack = builtins.list()
            _one_param = dest_screen, tuple(screen_args), builtins.dict(screen_kwargs)
            while True:
                if _one_param not in self._current_menu_stack:
                    break
                self._current_menu_stack.pop()
            self._current_menu_stack.append(_one_param)
            return renpy.run((self._tooltip_handler.DismissAction(), store.Scroll(u'tr3000_main_vpg', u'vertical decrease', getattr(sys, u'maxint', int(10000000000.0))), store.ShowMenu(dest_screen, *screen_args, **screen_kwargs)))

        def ConfirmAction(self, message, action):
            return store.Function(self._confirm, message, action)

        def BackAction(self):
            return store.Function(self._back)

        def ForwardAction(self, dest_screen, *screen_args, **screen_kwargs):
            return store.Function(self._forward, dest_screen, *screen_args, **screen_kwargs)

        def ApplySettingAction(self, restart_prescan_thread=False, update_work_method=False, language_check=False, interrupt_translations=False, restart=True, recalculate_choice_menu=False):
            funcs = self._translator._dump_setting, self._translator._check_setting
            funcs = builtins.list(funcs)
            if restart_prescan_thread:
                funcs.append(self._translator._translate_preparer.restart)
            if update_work_method:
                funcs.append(self._translator.update_work_method)
            if language_check:
                funcs.append(self._translator._directions_language_check)
            if interrupt_translations:
                funcs.append(self._translator._translator_object.interrupt_all_translations)
            if recalculate_choice_menu:

                def recalc():
                    self._choice_menu_object.update_all_menu(self._translator._setting[u'showMenuInfo'])
                funcs.append(recalc)
            result = builtins.list(map(store.Function, funcs))
            if restart:
                result.append(store._translator3000.Translator3000.NeedRestartAction())
            return tuple(result)

        def is_correct_font(self, renpy_path_to_font):
            if renpy.game.context().init_phase:
                raise Exception(u'This method use render and not work in init.')
            filename = self._fs_object._normpath(renpy_path_to_font).replace(u'\\', u'/')
            if not self._translator.is_loadable(filename):
                return False
            try:
                renpy.render(store.Text(u'Test', font=filename), renpy.config.screen_width, renpy.config.screen_height, 0, 0)
            except Exception as ex:
                return False
            else:
                return True

        def _set_font_pref(self, font, from_renpy=True, save_name=None):
            font = self._fs_object._normpath(font)
            font = font.replace(u'\\', u'/')
            if not font.strip():
                raise ValueError(self.translate(u'\u0424\u0430\u0439\u043b \u0448\u0440\u0438\u0444\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.'))
            for _check in (True, False, u'from_database'):
                if from_renpy == _check:
                    break
            else:
                raise ValueError(u'Incorrect param {0}'.format(from_renpy))
            if not save_name:
                save_name = font
            if from_renpy:
                if from_renpy is True:
                    if not self.is_correct_font(font):
                        return
                    with utils.renpy_open(font) as _fileobj:
                        self._translator._fonts.add_font(save_name, fileobj=_fileobj)
                set_dict = self._translator._setting[u'extraTextOptions']
                set_dict[u'font'] = save_name
                return renpy.run(self.ApplySettingAction())
            font = path.abspath(font)
            if not path.isfile(font):
                raise ValueError(self.translate(u'\u0424\u0430\u0439\u043b \u0448\u0440\u0438\u0444\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.'))
            with open(font, u'rb') as _file:
                self._translator._fonts.add_font(save_name, fileobj=_file)
            return self._set_font_pref(font, from_renpy=u'from_database', save_name=save_name)

        @staticmethod
        def parse_size_format(value):
            modifier = u''
            value = unicode(value)
            if value[0] in u'+-':
                modifier, value = value[0], value[1:]
            if not value.isdigit():
                _msg = self.translate(u"\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435 '{0}' \u0434\u043e\u043b\u0436\u043d\u043e \u0431\u044b\u0442\u044c \u0447\u0438\u0441\u043b\u043e\u043c.")
                raise ValueError(_msg.format(value))
            return (int(value), modifier)

        @property
        def _text_size_pref(self):
            _default_value = 20
            size = self._translator._setting[u'extraTextOptions'][u'size']
            if size is None:
                size = _default_value
            value, mod = self.parse_size_format(size)
            if mod:
                return _default_value
            return int(value)

        @_text_size_pref.setter
        def _text_size_pref(self, new_size):
            value, mod = self.parse_size_format(new_size)
            if mod:
                raise ValueError(self.translate(u'\u041c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u044b `+`/`-` \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u044e\u0442\u0441\u044f.'))
            self._translator._setting[u'extraTextOptions'][u'size'] = value
            renpy.run(self.ApplySettingAction())

        @property
        def requests_frequency_pref(self):
            frq = self._translator._setting[u'requestsFrequency']
            if frq is None:
                frq = store._translator3000.current_session.__class__.RPM
            return float(frq)

        @requests_frequency_pref.setter
        def requests_frequency_pref(self, new_freq):
            new_freq = float(new_freq)
            self._translator._setting[u'requestsFrequency'] = new_freq
            renpy.run(self.ApplySettingAction())

        @property
        def gui_language(self):
            if self._translator._multi_persistent.gui_language is None:
                self._translator._multi_persistent.gui_language = u'english'
                self._translator._multi_persistent.save()
            return self._translator._multi_persistent.gui_language

        @gui_language.setter
        def gui_language(self, new_language):
            new_language = new_language.strip().lower()
            if new_language not in self.available_languages:
                raise ValueError(u"Incorrect lang '{0}'.".format(new_language))
            if new_language != self.gui_language:
                self._translator._multi_persistent.gui_language = new_language
                self._translator._multi_persistent.save()
                self._sample_text = self.translate(self._original_sample_text)
            renpy.run(self.ApplySettingAction(recalculate_choice_menu=True))

        @property
        def show(self):
            return self._m1_0x3ctranslator30000x3e__show

        @show.setter
        def show(self, new_status):
            self._m1_0x3ctranslator30000x3e__show = bool(new_status)

        @staticmethod
        def get_persistent_name(name):
            return u'translator3000_{0}'.format(name)

        @staticmethod
        def game_passing_percentage():
            a = builtins.max(float(renpy.count_seen_dialogue_blocks()), 0.0)
            b = builtins.max(float(renpy.count_dialogue_blocks()), 1.0)
            return a / b

        def translate(self, text, language=None, not_translate_mark=True):
            if not isinstance(text, basestring):
                raise TypeError(u"'text' should be a string.")
            if isinstance(text, bytes):
                text = text.decode(u'utf_8')
            if language is None:
                language = self.gui_language
            if language not in self.available_languages:
                raise ValueError(u"Incorrect language '{0}'.".format(language))
            language = u'translator3000_{0}'.format(language)
            result = renpy.translation.translate_string(text, language=language)
            if not_translate_mark:
                result = u'###notTranslate###{0}'.format(result)
            return result


    class _DragObjectData(store.NoRollback):
        __author__ = u'Vladya'
        TEXT_STYLE_DEFAULT = __renpy__dict__({u'size': style.translator3000_text.size})

        def __init__(self, name):
            self._m1_0x3ctranslator30000x3e__name = name.strip()

        def __getattr__(self, attr):
            if attr in self.TEXT_STYLE_DEFAULT:
                return self._text_style_props[attr]
            raise AttributeError(attr)

        def __setattr__(self, attr, new_value):
            if attr in self.TEXT_STYLE_DEFAULT:
                dct = copy.deepcopy(self._text_style_props)
                dct[attr] = new_value
                self._text_style_props = dct
                return
            return super(_DragObjectData, self).__setattr__(attr, new_value)

        @property
        def _persistent_name(self):
            return u'_tr3000_{0}'.format(self._m1_0x3ctranslator30000x3e__name)

        @property
        def persistent(self):
            return getattr(persistent, self._persistent_name, None)

        @persistent.setter
        def persistent(self, new_value):
            return setattr(persistent, self._persistent_name, new_value)

        @property
        def x(self):
            if self.persistent is None:
                return 0
            return self.persistent[0]

        @property
        def y(self):
            if self.persistent is None:
                return int(store.config.screen_height // 2)
            return self.persistent[1]

        @property
        def w(self):
            if self.persistent is None:
                return 0
            return self.persistent[2]

        @property
        def h(self):
            if self.persistent is None:
                return 0
            return self.persistent[3]

        @property
        def _text_align(self):
            x_area = float(store.config.screen_width)
            x_area -= float(self.w)
            if x_area == 0.0:
                return 0.0
            if float(self.x) / x_area <= 0.5:
                return 0.0
            return 1.0

        def _dragged(self, drags, drop):
            for dr in drags:
                self.persistent = dr.x, dr.y, dr.w, dr.h
            renpy.restart_interaction()

        @property
        def _text_style_props(self):
            name = u'_tr3000_{0}_text_style'.format(self._m1_0x3ctranslator30000x3e__name)
            value = getattr(persistent, name, None)
            if value is None:
                return self.TEXT_STYLE_DEFAULT
            return value

        @_text_style_props.setter
        def _text_style_props(self, new_value):
            name = u'_tr3000_{0}_text_style'.format(self._m1_0x3ctranslator30000x3e__name)
            setattr(persistent, name, new_value)


    class ColorPicker(renpy.Displayable, store.NoRollback):
        __author__ = u'Vladya'
        focusable = True

        def __init__(self, gui_object, _ch_dict=None, _key=None, **properties):
            properties.setdefault(u'style', u'translator3000_default')
            super(ColorPicker, self).__init__(**properties)
            self._m1_0x3ctranslator30000x3e__current_coor = None
            self._m1_0x3ctranslator30000x3e__current_color = None
            self._m1_0x3ctranslator30000x3e__is_pressed = False
            self._m1_0x3ctranslator30000x3e__brightness = 0.0
            self._gui_object = gui_object
            self._translator = gui_object._translator
            self._m1_0x3ctranslator30000x3e__changed_dict = _ch_dict
            self._m1_0x3ctranslator30000x3e__dict_key = _key

        def __call__(self, _ch_dict, _key):
            return ColorPicker(self._gui_object, _ch_dict, _key)

        def _callback(self, color):
            assert self._m1_0x3ctranslator30000x3e__changed_dict is not None
            actions = builtins.list()
            act = store.SetDict(self._m1_0x3ctranslator30000x3e__changed_dict, self._m1_0x3ctranslator30000x3e__dict_key, color.hexcode)
            actions.append(act)
            actions.append(self._gui_object.ApplySettingAction())
            renpy.run(tuple(actions))

        def _redraw(self):
            if self._m1_0x3ctranslator30000x3e__current_coor:
                prev = self._m1_0x3ctranslator30000x3e__current_color
                self._m1_0x3ctranslator30000x3e__current_color = self._get_pixel(force_ff_alpha=True, *self._m1_0x3ctranslator30000x3e__current_coor)
                if prev != self._m1_0x3ctranslator30000x3e__current_color:
                    self._callback(self._m1_0x3ctranslator30000x3e__current_color)
            renpy.redraw(self, 0.0)

        @property
        def color_circle(self):
            return renpy.display.im.MatrixColor(self._gui_object.loader.colorCircle, renpy.display.im.matrix.brightness(self.brightness))

        @property
        def color_circle_size(self):
            surf = renpy.load_surface(self.color_circle)
            return tuple(map(int, surf.get_size()))

        @property
        def current_color(self):
            if self._m1_0x3ctranslator30000x3e__current_color is None:
                return renpy.color.Color((0, 0, 0, 0))
            return self._m1_0x3ctranslator30000x3e__current_color

        @property
        def brightness(self):
            return self._m1_0x3ctranslator30000x3e__brightness

        @brightness.setter
        def brightness(self, level):
            self._m1_0x3ctranslator30000x3e__brightness = float(level)
            self._redraw()

        def _get_pixel(self, x, y, force_ff_alpha=False):
            x, y = map(int, (x, y))
            surf = renpy.load_surface(self.color_circle)
            try:
                result = surf.get_at((x, y))
            except IndexError:
                return renpy.color.Color((0, 0, 0, 0))
            else:
                r, g, b, a = result
            if force_ff_alpha:
                a = 255
            return renpy.color.Color((r, g, b, a))

        def set_coor(self, x, y, is_offset=False):
            if is_offset:
                if not self._m1_0x3ctranslator30000x3e__current_coor:
                    return
                old_x, old_y = self._m1_0x3ctranslator30000x3e__current_coor
                x += old_x
                y += old_y
            x, y = map(float, (x, y))
            surf = renpy.load_surface(self.color_circle)
            width, height = map(float, surf.get_size())
            xcenter, ycenter = width / 2.0, height / 2.0
            xcenter_dist = xcenter - x
            ycenter_dist = ycenter - y
            dist = math.hypot(*map(abs, (xcenter_dist, ycenter_dist)))
            if dist:
                xstep = xcenter_dist / dist
                ystep = ycenter_dist / dist
            else:
                xstep = ystep = 0.0
            while True:
                variant = tuple(map(int, map(round, (x, y))))
                try:
                    r, g, b, _alpha = surf.get_at(variant)
                except IndexError:
                    pass
                else:
                    if _alpha:
                        self._m1_0x3ctranslator30000x3e__current_coor = variant
                        return
                x += xstep
                y += ystep

        def event(self, ev, x, y, st):
            grabbed = renpy.display.focus.get_grab() is self
            ignore_event = False
            if grabbed:
                if ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                    self.set_coor(x, y)
                    ignore_event = True
                elif renpy.map_event(ev, u'bar_up'):
                    self.set_coor(0, -1, is_offset=True)
                    ignore_event = True
                elif renpy.map_event(ev, u'bar_down'):
                    self.set_coor(0, 1, is_offset=True)
                    ignore_event = True
                elif renpy.map_event(ev, u'bar_left'):
                    self.set_coor(-1, 0, is_offset=True)
                    ignore_event = True
                elif renpy.map_event(ev, u'bar_right'):
                    self.set_coor(1, 0, is_offset=True)
                    ignore_event = True
                if renpy.map_event(ev, u'bar_deactivate'):
                    renpy.display.focus.set_grab(None)
                    ignore_event = True
            elif self.is_focused() and renpy.map_event(ev, u'bar_activate'):
                renpy.display.focus.set_grab(self)
                self.set_coor(x, y)
                ignore_event = True
            if ignore_event:
                self._redraw()
                raise renpy.IgnoreEvent()
            return None

        def visit(self):
            return __renpy__list__([self.color_circle])

        def per_interact(self):
            self._redraw()

        def render(self, *rend_args):
            back = renpy.render(self.color_circle, *rend_args)
            w, h = tuple(map(int, back.get_size()))
            result = renpy.Render(w, h)
            result.blit(back, (0, 0))
            if self._m1_0x3ctranslator30000x3e__current_coor:
                x, y = self._m1_0x3ctranslator30000x3e__current_coor
                canvas = result.canvas()
                canvas.circle(u'#000', (x, y), 15)
                canvas.circle(self.current_color, (x, y), 3)
            result.add_focus(self, None, 0, 0, w, h, 0, 0, back)
            return result


    class _LastSayEditValue(store.InputValue):
        __author__ = u'Vladya'

        def __init__(self, _db_dict, _keys, enter_action, translator_obj):
            self._m1_0x3ctranslator30000x3e__db_dict = _db_dict
            self._m1_0x3ctranslator30000x3e__keys = _keys
            self._m1_0x3ctranslator30000x3e__enter_action = enter_action
            self._m1_0x3ctranslator30000x3e__translator_object = translator_obj
            self._m1_0x3ctranslator30000x3e__translated_mark = None

        @property
        def is_translated_mark(self):
            self.get_text()
            return self._m1_0x3ctranslator30000x3e__translated_mark

        def get_text(self):
            source_lang, edit_t, dest_lang = self._m1_0x3ctranslator30000x3e__keys
            if source_lang in self._m1_0x3ctranslator30000x3e__db_dict:
                if edit_t in self._m1_0x3ctranslator30000x3e__db_dict[source_lang]:
                    if dest_lang in self._m1_0x3ctranslator30000x3e__db_dict[source_lang][edit_t]:
                        self._m1_0x3ctranslator30000x3e__translated_mark = True
                        return self._m1_0x3ctranslator30000x3e__db_dict[source_lang][edit_t][dest_lang]
            self._m1_0x3ctranslator30000x3e__translated_mark = False
            return edit_t

        def set_text(self, s):
            source_lang, edit_t, dest_lang = self._m1_0x3ctranslator30000x3e__keys
            if source_lang not in self._m1_0x3ctranslator30000x3e__db_dict:
                self._m1_0x3ctranslator30000x3e__db_dict[source_lang] = builtins.dict()
            if edit_t not in self._m1_0x3ctranslator30000x3e__db_dict[source_lang]:
                self._m1_0x3ctranslator30000x3e__db_dict[source_lang][edit_t] = builtins.dict()
            self._m1_0x3ctranslator30000x3e__db_dict[source_lang][edit_t][dest_lang] = s
            renpy.restart_interaction()

        def enter(self):
            if self._m1_0x3ctranslator30000x3e__enter_action:
                renpy.run(self._m1_0x3ctranslator30000x3e__enter_action)
            return super(_LastSayEditValue, self).enter()

        @classmethod
        def _create_value_object(cls, enter_action=None, _tr=None):
            if not hasattr(store, u'_last_raw_what'):
                return None
            current_text = store._last_raw_what
            if not isinstance(current_text, basestring):
                return None
            if not _tr:
                _tr = getattr(store, u'translator3000')
            if current_text not in _tr._original_mapping:
                return None
            _i, edit_t = _tr._original_mapping[current_text]
            _source_lang = _tr.game_language
            _dest_lang = _tr.direction_of_translation
            for _service in _tr._get_translation_services(only_available=True):
                serv_tr = _tr._translator_object._get_translator(_service)
                source_lang = serv_tr.get_lang_code(_source_lang, False)
                dest_lang = serv_tr.get_lang_code(_dest_lang, True)
                with serv_tr._database_lock:
                    if source_lang not in serv_tr._database:
                        continue
                    if edit_t not in serv_tr._database[source_lang]:
                        continue
                    if dest_lang not in serv_tr._database[source_lang][edit_t]:
                        continue
                    return cls(serv_tr._database, (source_lang, edit_t, dest_lang), enter_action, _tr)
            return None


    class _PressedKey(store.NoRollback):
        __author__ = u'Vladya'
        MODIFIERS = tuple(map(lambda a: (a, getattr(pygame, u'KMOD_{0}'.format(a.upper()))), sorted((u'alt', u'meta', u'shift', u'ctrl'))))
        KEYS = builtins.dict(map(lambda a: (a[1], a[0][len(u'K_'):]), filter(lambda b: b[0].startswith(u'K_'), pygame.__dict__.items())))
        MODS_AS_KEYS = builtins.dict(alt=(u'RALT', u'LALT'), meta=(u'RMETA', u'LMETA', u'RSUPER', u'LSUPER'), shift=(u'RSHIFT', u'LSHIFT'), ctrl=(u'RCTRL', u'LCTRL'))

        def __init__(self, key_event=None, data_from_setting=None):
            if data_from_setting:
                if isinstance(data_from_setting, basestring):
                    self._m1_0x3ctranslator30000x3e__keycode = self._get_keycode(data_from_setting)
                    self._m1_0x3ctranslator30000x3e__modbits = 0
                elif isinstance(data_from_setting, builtins.dict):
                    _key = data_from_setting[u'mainKey']
                    _mods = data_from_setting.get(u'extraKeys', None)
                    self._m1_0x3ctranslator30000x3e__keycode = self._get_keycode(_key)
                    self._m1_0x3ctranslator30000x3e__modbits = self._get_modbits(_mods)
                else:
                    raise TypeError(data_from_setting)
            elif key_event:
                self._m1_0x3ctranslator30000x3e__keycode = key_event.key
                self._m1_0x3ctranslator30000x3e__modbits = key_event.mod
            else:
                raise ValueError(u'No argument is passed.')

        @staticmethod
        def _get_keycode(name):
            assert isinstance(name, basestring)
            name = name.strip()
            if name.upper().startswith(u'K_'):
                name = name[len(u'K_'):]
            if len(name) <= 1:
                name = name.lower()
            else:
                name = name.upper()
            name = u'K_{0}'.format(name)
            return getattr(pygame, name)

        @classmethod
        def _get_modbits(cls, mods):
            result = 0
            for mod in mods:
                mod = mod.strip().upper()
                if mod.startswith(u'KMOD_'):
                    mod = mod[len(u'KMOD_'):]
                mod_bitmask = getattr(pygame, u'KMOD_{0}'.format(mod))
                result |= mod_bitmask
            return result

        @property
        def as_setting_param(self):
            mods = self.mods
            if mods:
                return builtins.dict(extraKeys=builtins.list(mods), mainKey=self.name)
            else:
                return self.name

        @property
        def keycode(self):
            return self._m1_0x3ctranslator30000x3e__keycode

        @property
        def name(self):
            if self.keycode in self.KEYS:
                return self.KEYS[self.keycode]
            return None

        @property
        def modbits(self):
            return self._m1_0x3ctranslator30000x3e__modbits

        @property
        def mods(self):
            name = self.name
            result = builtins.list()
            for mod_name, bitmask in self.MODIFIERS:
                if name in self.MODS_AS_KEYS[mod_name]:
                    continue
                if self.modbits & bitmask:
                    result.append(mod_name)
            return tuple(result)

        @property
        def command(self):
            result = u''
            for mod_name in self.mods:
                result += mod_name
                result += u'_'
            result += u'K_{0}'.format(self.name)
            return result

        def __eq__(self, other):
            if not isinstance(other, _PressedKey):
                return False
            if self.keycode != other.keycode:
                return False
            if self.modbits != other.modbits:
                return False
            return True

        def __ne__(self, other):
            return not self == other

        def __repr__(self):
            return u'<_PressedKey: {0.command}>'.format(self)


    class PressKeyAnalyzer(renpy.display.layout.Null, store.NoRollback):
        __author__ = u'Vladya'

        def __init__(self, pressed_data=None, default_value=None):
            super(PressKeyAnalyzer, self).__init__(style=u'translator3000_default')
            self._m1_0x3ctranslator30000x3e__pressed = None
            self._m1_0x3ctranslator30000x3e__default = None
            if pressed_data:
                self._m1_0x3ctranslator30000x3e__pressed = _PressedKey(data_from_setting=pressed_data)
            if default_value:
                self._m1_0x3ctranslator30000x3e__default = _PressedKey(data_from_setting=default_value)

        @property
        def pressed(self):
            return self._m1_0x3ctranslator30000x3e__pressed

        @pressed.setter
        def pressed(self, new_value):
            if new_value:
                if not isinstance(new_value, _PressedKey):
                    raise TypeError(u'Incorrect data. ')
                self._m1_0x3ctranslator30000x3e__pressed = new_value
            else:
                self._m1_0x3ctranslator30000x3e__pressed = None

        @property
        def default_pressed(self):
            return self._m1_0x3ctranslator30000x3e__default

        def event(self, ev, x, y, st):
            if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                if ev.type == pygame.KEYDOWN:
                    self.pressed = _PressedKey(key_event=ev)
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()
    ElementInfo = collections.namedtuple(u'ElementInfo', (u'fn', u'height', u'matrices', u'rotate', u'recolor'))


    class GUILoader(SingleTone):
        __author__ = u'Vladya'
        GUI_FOLDER = posixpath.normpath(u'Translator3000OtherFiles/mainGUI1')
        DEFAULT_HOVER_MATRICES = im.matrix.brightness(0.3),
        IMAGE_CACHE = builtins.dict()
        CACHE_LOCK = threading.Lock()
        ELEMENT_RULES = builtins.dict(mainMark=ElementInfo(u'mainMark1', 35, None, None, True), buttonBack=ElementInfo(u'buttonBack', 40, None, None, True), minimizeButtonElement=ElementInfo(u'arrowUp', 15, None, 90, True), maximizeButtonElement=ElementInfo(u'arrowUp', 15, None, 270, True), closeButtonElement=ElementInfo(u'closeButtonElement', 20, None, None, True), mainMenuBack=ElementInfo(u'mainMenuBack', 40, None, None, True), mainMenuForward=ElementInfo(u'mainMenuForward', 40, None, None, True), mainMenuDocs=ElementInfo(u'mainMenuDocs', 40, None, None, True), themeSwitcher=ElementInfo(u'themeSwitcher', 40, None, None, True), refreshPage=ElementInfo(u'refreshPage', 40, None, None, True), vbar=ElementInfo(u'vbar', None, None, None, True), vbarThumb=ElementInfo(u'vbarThumb', None, None, None, True), hbarEmpty=ElementInfo(u'hbarEmpty', None, None, None, True), hbarFull=ElementInfo(u'hbarFull', None, None, None, True), backupDB=ElementInfo(u'backupDB', 90, None, None, True), clearLocalCache=ElementInfo(u'clearLocalCache', 90, None, None, True), clearAllCache=ElementInfo(u'clearAllCache', 90, None, None, True), changeInterfaceLang=ElementInfo(u'changeInterfaceLang', 90, None, None, True), translatorSetting=ElementInfo(u'translatorSetting', 90, None, None, True), supportDeveloper=ElementInfo(u'supportDeveloper', 90, None, None, True), supportDeveloper2=ElementInfo(u'supportDeveloper2', 90, None, None, True), supportDeveloper3=ElementInfo(u'supportDeveloper3', 90, None, None, True), supportDeveloper4=ElementInfo(u'supportDeveloper4', 90, None, None, True), statButton=ElementInfo(u'statButton', 90, None, None, True), statButton2=ElementInfo(u'statButton2', 90, None, None, True), statButton2ReadAll=ElementInfo(u'statButton2', 90, (im.matrix.invert(),), None, True), variablesEditor=ElementInfo(u'variablesEditor', 90, None, None, True), textEditorWindow=ElementInfo(u'textEditorWindow', 90, None, None, True), menuExpand=ElementInfo(u'menuExpand', 90, None, None, False), arrowUp=ElementInfo(u'arrowUp', 17, None, None, True), arrowDown=ElementInfo(u'arrowUp', 17, None, 180, True), checkBoxBack=ElementInfo(u'checkBoxBack', 20, None, None, True), checkBoxMark=ElementInfo(u'checkBoxMark', 20, None, None, True), questionMark=ElementInfo(u'questionMark', 25, None, None, True), settingBack=ElementInfo(u'settingBack', None, None, None, True), radioNo=ElementInfo(u'radioNo', 30, None, None, True), radioYes=ElementInfo(u'radioYes', 30, None, None, True), leftSideBackground=ElementInfo(u'checkbox2Back', 50, None, None, True), checkbox2Back=ElementInfo(u'checkbox2Back', 30, None, None, True), checkbox2BackHover=ElementInfo(u'checkbox2BackHover', 30, None, None, True), checkbox2Mark=ElementInfo(u'checkbox2Mark', 12, None, None, True), checkbox2MarkHover=ElementInfo(u'checkbox2MarkHover', 12, None, None, True), colorCircle=ElementInfo(u'colors', 280, None, None, False), clockBarBack1=ElementInfo(u'clockBarBack', 40, None, None, True), clockBarArrow1=ElementInfo(u'clockBarArrow', 40, None, None, True), zoomMinus=ElementInfo(u'zoomMinus', 18, None, None, True), zoomPlus=ElementInfo(u'zoomPlus', 18, None, None, True), messagePassive=ElementInfo(u'messagesIcon', 48, None, None, True), messageActive=ElementInfo(u'messagesUnread', 48, None, None, True), searchClear=ElementInfo(u'closeButtonElement', 20, None, None, True), searchFavorite=ElementInfo(u'favoriteIdle', 30, None, None, True), searchFavoriteSelected=ElementInfo(u'favoriteSelected', 30, None, None, True))

        def __getattr__(self, attr, extra_matrix=None):
            if attr.startswith(u'__') and attr.endswith(u'__'):
                raise AttributeError(attr)

            def _apply_properties(k, create_auto_hover=False):
                info = self.ELEMENT_RULES[k]
                _key = info, create_auto_hover, extra_matrix
                if _key not in self.IMAGE_CACHE:
                    _im = info.fn
                    if isinstance(_im, basestring):
                        _im = self._get_image_fn(_im)
                    _im = self._get_imagebase(_im)
                    if info.matrices:
                        for _matrix in info.matrices:
                            _im = im.MatrixColor(_im, _matrix, style=u'translator3000_default')
                    if create_auto_hover:
                        for _matrix in self.DEFAULT_HOVER_MATRICES:
                            _im = im.MatrixColor(_im, _matrix, style=u'translator3000_default')
                    _zoom = None
                    if info.height is not None:
                        _zoom = self._calculate_zoom(_im, info.height)
                    if info.rotate is not None:
                        if _zoom is None:
                            _zoom = 1.0
                        _im = im.Rotozoom(_im, info.rotate, _zoom, style=u'translator3000_default')
                    elif _zoom is not None:
                        _im = im.FactorScale(_im, _zoom, style=u'translator3000_default')
                    _matrix = im.matrix.identity()
                    if info.recolor:
                        _matrix = self._get_recolor_matrix()
                        if extra_matrix:
                            _matrix *= extra_matrix
                    self.IMAGE_CACHE[_key] = im.MatrixColor(_im, _matrix, align=(0.5, 0.5), style=u'translator3000_default')
                return self.IMAGE_CACHE[_key]
            with self.CACHE_LOCK:
                if attr in self.ELEMENT_RULES:
                    return _apply_properties(attr)
                if attr.endswith(u'Hover'):
                    idle_name = attr[:-len(u'Hover')]
                    if idle_name in self.ELEMENT_RULES:
                        return _apply_properties(idle_name, True)
            raise AttributeError(attr)

        def _clear_cache(self):
            with self.CACHE_LOCK:
                self.IMAGE_CACHE.clear()

        @staticmethod
        def _get_imagebase(data):
            store._translator3000.Translator3000._arch_fix(_raise=True)
            result = renpy.easy.displayable(data)
            if not isinstance(result, im.ImageBase):
                raise TypeError(data)
            return result

        @classmethod
        def _get_recolor_matrix(cls, target_color=None):
            if target_color is None:
                target_color = theme.main_color
            START_COLOR = Color2(u'#000084')
            target_color = Color2(target_color)
            value = (target_color.hsv[0] - START_COLOR.hsv[0]) % 1.0 * 360.0
            result = im.matrix.hue(value)
            return result

        @classmethod
        def _calculate_zoom(cls, im_data, need_height_for_1080):
            im_data = cls._get_imagebase(im_data)
            need_height = resize_from_1080(float(need_height_for_1080), 5.0)
            if not renpy.display.draw:
                _types = tuple(map(lambda y: getattr(im, y), filter(lambda x: hasattr(im, x), (u'AlphaMask', u'Recolor', u'MatrixColor', u'Blur', u'Twocolor', u'Map', u'Flip'))))
                while True:
                    if isinstance(im_data, _types):
                        if hasattr(im_data, u'image'):
                            im_data = im_data.image
                            continue
                    break
                if isinstance(im_data, im.Composite):
                    _w, h = map(float, im_data.size)
                    return need_height / h
            surf = im_data.load()
            _w, h = map(float, surf.get_size())
            return need_height / h

        @classmethod
        def _get_gui_fn(cls, _fn, _check=u'raise'):
            fn = posixpath.join(cls.GUI_FOLDER, posixpath.normpath(_fn))
            if not _check:
                return fn
            store._translator3000.Translator3000._arch_fix(_raise=True)
            if store._translator3000.Translator3000.is_loadable(fn):
                return fn
            if _check == u'raise':
                raise Exception(_fn)
            return None

        @classmethod
        def _get_image_fn(cls, _element_name, default_ext=None):
            element_name = posixpath.normpath(_element_name)
            element_name, _ext = posixpath.splitext(element_name)
            for ext in (u'.png', u'.jpg', u'.jpeg', u'.webp'):
                fn = cls._get_gui_fn(u''.join((element_name, ext)), True)
                if fn is None:
                    continue
                return fn
            if default_ext:
                return cls._get_gui_fn(u''.join((element_name, default_ext)), _check=False)
            raise Exception(_element_name)


    class Color2(renpy.color.Color):
        __author__ = u'Vladya'
        RYB_WHEEL = 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 23, 24, 24, 25, 25, 26, 27, 27, 28, 28, 29, 29, 30, 30, 31, 32, 32, 33, 33, 34, 34, 35, 35, 36, 36, 36, 37, 37, 38, 38, 38, 39, 39, 40, 40, 40, 41, 41, 41, 42, 42, 43, 43, 43, 44, 44, 45, 45, 45, 46, 46, 46, 47, 47, 48, 48, 48, 49, 49, 49, 50, 50, 51, 51, 51, 52, 52, 52, 53, 53, 54, 54, 54, 55, 55, 55, 56, 56, 57, 57, 57, 58, 58, 58, 59, 59, 59, 60, 61, 62, 63, 65, 66, 67, 68, 70, 71, 72, 73, 75, 76, 77, 79, 80, 81, 82, 84, 85, 86, 88, 89, 90, 91, 93, 94, 95, 97, 98, 99, 100, 100, 101, 102, 103, 103, 104, 105, 105, 106, 107, 107, 108, 109, 110, 110, 111, 112, 112, 113, 114, 114, 115, 116, 117, 117, 118, 119, 119, 120, 121, 121, 122, 122, 123, 123, 124, 125, 125, 126, 126, 127, 127, 128, 128, 129, 130, 130, 131, 131, 132, 132, 133, 134, 134, 135, 135, 136, 136, 137, 137, 139, 141, 143, 145, 147, 149, 151, 153, 154, 156, 158, 160, 162, 164, 166, 168, 170, 172, 174, 176, 178, 180, 182, 183, 185, 187, 189, 191, 192, 194, 196, 198, 200, 201, 203, 206, 208, 211, 214, 216, 219, 221, 224, 227, 229, 232, 234, 237, 240, 242, 245, 248, 251, 253, 256, 259, 261, 264, 267, 269, 270, 271, 272, 273, 273, 274, 275, 276, 276, 277, 278, 279, 280, 280, 281, 282, 283, 284, 284, 285, 286, 287, 287, 288, 289, 290, 291, 291, 292, 293, 294, 294, 295, 296, 297, 298, 298, 299, 300, 301, 303, 304, 306, 307, 309, 310, 311, 313, 314, 316, 317, 319, 320, 321, 323, 324, 326, 327, 329, 330, 332, 334, 335, 337, 339, 341, 342, 344, 346, 348, 349, 351, 353, 355, 357

        @classmethod
        def _ryb_hue2rgb(cls, input_value):
            input_value = float(input_value) % 1.0 * 360.0
            ind1 = int(input_value) % 360
            ind2 = (ind1 + 1) % 360
            value1 = float(cls.RYB_WHEEL[ind1])
            value2 = float(cls.RYB_WHEEL[ind2])
            addition = (value2 - value1) * (input_value % 1.0)
            return (value1 + addition) / 360.0 % 360.0

        @classmethod
        def _rgb_hue2ryb(cls, input_value):
            input_value = float(input_value) % 1.0 * 360.0
            result = 0
            for i, val in enumerate(map(float, cls.RYB_WHEEL)):
                if input_value <= val:
                    result = i
                    break
            return result / 360.0 % 360.0

        @property
        def rgba(self):
            try:
                result = super(Color2, self).rgba
            except AttributeError:
                result = self.rgb + (self.alpha,)
            return result

        def _m1_0x3ctranslator30000x3e__get_crop_palette(self, size, monochromatic_size=1):
            multipler = 1.0 / float(size)
            result = builtins.list()
            for _color in self.get_monochromatic_palette(monochromatic_size, delete_first=False):
                h, s, v = _color.hsv
                h = _color._rgb_hue2ryb(h)
                for i in map(float, range(size)):
                    _h = _color._ryb_hue2rgb((h + multipler * i) % 1.0)
                    result.append(Color2(hsv=(_h, s, v)))
            return tuple(result)

        def get_monochromatic_palette(self, size, delete_first=True):
            h, s, v = self.hsv
            if delete_first:
                size += 1
            multipler = 1.0 / float(size)
            result = builtins.list()
            for i in map(float, range(size)):
                _s = s - multipler * i
                _v = v - multipler * i
                if _s > 1.0:
                    _s = -_s % 1.0
                elif _s < 0.0:
                    _s = -_s
                if _v > 1.0:
                    _v = -_v % 1.0
                elif _v < 0.0:
                    _v = -_v
                result.append(Color2(hsv=(h, _s, _v)))
            if delete_first:
                result = result[1:]
            return tuple(result)

        def get_complementary_palette(self, size):
            size += 1
            monochromatic_size = size // 2 + 1
            return self._m1_0x3ctranslator30000x3e__get_crop_palette(2, monochromatic_size)[1:size]

        def get_triad_palette(self, size):
            size += 1
            monochromatic_size = size // 3 + 1
            return self._m1_0x3ctranslator30000x3e__get_crop_palette(3, monochromatic_size)[1:size]

        def get_square_palette(self, size):
            size += 1
            monochromatic_size = size // 4 + 1
            return self._m1_0x3ctranslator30000x3e__get_crop_palette(4, monochromatic_size)[1:size]

        def get_similarity_palette(self, size):
            size += 1
            monochromatic_size = size // 5 + 1
            STEP = 0.08333333333333333
            result = builtins.list()
            for _color in self.get_monochromatic_palette(monochromatic_size, delete_first=False):
                h, s, v = _color.hsv
                h = _color._rgb_hue2ryb(h)
                for step in (0.0, 1.0, -1.0, 2.0, -2.0):
                    step *= STEP
                    _h = _color._ryb_hue2rgb((h + step) % 1.0)
                    result.append(Color2(hsv=(_h, s, v)))
            return tuple(result[1:size])


    class ClockBar(renpy.display.behavior.Bar, store.NoRollback):
        __author__ = u'Vladya'

        def __init__(self, back, arrow, back_rotate_point, arrow_rotate_point, _rotate_range=None, **extra_kw):
            for not_apply in (u'page', u'vertical'):
                if not_apply in extra_kw:
                    raise ValueError(u'{0} not apply to this displayable'.format(not_apply))
            extra_kw.setdefault(u'style', u'empty')
            extra_kw.setdefault(u'focus_mask', True)
            super(ClockBar, self).__init__(**extra_kw)
            self._m1_0x3ctranslator30000x3e__back = renpy.easy.displayable(back)
            self._m1_0x3ctranslator30000x3e__arrow = renpy.easy.displayable(arrow)
            self._m1_0x3ctranslator30000x3e__back_rotate_point = back_rotate_point
            self._m1_0x3ctranslator30000x3e__arrow_rotate_point = arrow_rotate_point
            if _rotate_range is None:
                _rotate_range = -90, 90
            _rng_min, _rng_max = map(lambda x: int(x) % 360, _rotate_range)
            self._m1_0x3ctranslator30000x3e__rotate_point_zero = _rng_min
            self._m1_0x3ctranslator30000x3e__rotate_range = (_rng_max - _rng_min) % 360
            assert self._m1_0x3ctranslator30000x3e__rotate_range > 0

        @property
        def rotate(self):
            coef = float(self.adjustment.value) / float(self.adjustment.range)
            result = float(self._m1_0x3ctranslator30000x3e__rotate_point_zero)
            result += float(self._m1_0x3ctranslator30000x3e__rotate_range) * coef
            return result

        def _get_rotate_from_coodinates(self, x, y):
            x1, y1 = map(float, self._m1_0x3ctranslator30000x3e__back_rotate_point)
            x2, y2 = map(float, (x, y))
            opposite = y2 - y1
            adjacent = x2 - x1
            if opposite == 0.0:
                angle = 0.0 if adjacent >= 0.0 else 180.0
            elif adjacent == 0.0:
                angle = 90.0 if opposite >= 0.0 else 270.0
            else:
                angle = math.degrees(math.atan2(opposite, adjacent))
            angle += 90.0
            return angle % 360.0

        def _rotate_to_value(self, rotate_value):
            coef = float((rotate_value - self._m1_0x3ctranslator30000x3e__rotate_point_zero) % 360.0)
            coef /= float(self._m1_0x3ctranslator30000x3e__rotate_range)
            if coef > 1.0:
                return None
            result = float(self.adjustment.range) * coef
            return result

        def event(self, ev, x, y, st):
            if not self.focusable:
                return None
            if not self.is_focused():
                return None
            if self.hidden:
                return None
            old_value = self.adjustment.value
            value = old_value
            grabbed = renpy.display.focus.get_grab() is self
            just_grabbed = False
            ignore_event = False
            if not grabbed and renpy.map_event(ev, u'bar_activate'):
                renpy.display.tts.speak(renpy.minstore.__(u'activate'))
                renpy.display.focus.set_grab(self)
                self.set_style_prefix(u'hover_', True)
                just_grabbed = True
                grabbed = True
                ignore_event = True
                renpy.exports.play(self.style.activate_sound)
            if grabbed:
                if renpy.map_event(ev, u'bar_up') or renpy.map_event(ev, u'bar_left'):
                    renpy.display.tts.speak(renpy.minstore.__(u'decrease'))
                    value -= self.adjustment.step
                    ignore_event = True
                elif renpy.map_event(ev, u'bar_down') or renpy.map_event(ev, u'bar_right'):
                    renpy.display.tts.speak(renpy.minstore.__(u'increase'))
                    value += self.adjustment.step
                    ignore_event = True
                elif ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                    rotate = self._get_rotate_from_coodinates(x, y)
                    new_value = self._rotate_to_value(rotate)
                    if new_value is not None:
                        value = new_value
                        ignore_event = True
                if not just_grabbed and renpy.map_event(ev, u'bar_deactivate'):
                    renpy.display.tts.speak(renpy.minstore.__(u'deactivate'))
                    renpy.display.focus.set_grab(None)
                    self.set_style_prefix(u'hover_', True)
                    ignore_event = True
                if value < 0:
                    renpy.display.tts.speak(u'')
                    value = 0
                if value > self.adjustment.range:
                    renpy.display.tts.speak(u'')
                    value = self.adjustment.range
                if isinstance(self.adjustment.range, int):
                    value = int(value)
            if hasattr(self.adjustment, u'round_value'):
                value = self.adjustment.round_value(value, release=True)
            if value != old_value:
                _changed = self.adjustment.change(value)
                if _changed is not None:
                    return _changed
            if ignore_event:
                raise renpy.IgnoreEvent()
            return None

        def visit(self):
            return __renpy__list__([self._m1_0x3ctranslator30000x3e__back, self._m1_0x3ctranslator30000x3e__arrow])

        @staticmethod
        def _place_func(*args, **kwargs):
            if hasattr(renpy.display, u'displayable'):
                if hasattr(renpy.display.displayable, u'place'):
                    return renpy.display.displayable.place(*args, **kwargs)
            return renpy.display.core.place(*args, **kwargs)

        def render(self, width, height, st, at):
            if self.value is not None:
                redraw = self.value.periodic(st)
                if redraw is not None:
                    renpy.redraw(self, redraw)
            back_rend = renpy.render(self._m1_0x3ctranslator30000x3e__back, width, height, st, at)
            w, h = tuple(map(int, back_rend.get_size()))
            self.width = w
            self.height = h
            result = renpy.Render(w, h)
            result.blit(back_rend, (0, 0))
            x, y = self._m1_0x3ctranslator30000x3e__back_rotate_point
            if not isinstance(x, (int, store.absolute)):
                x *= float(w)
            if not isinstance(y, (int, store.absolute)):
                y *= float(h)
            x, y = map(int, (x, y))
            self._m1_0x3ctranslator30000x3e__back_rotate_point = x, y
            arrow = store.Transform(self._m1_0x3ctranslator30000x3e__arrow, rotate=self.rotate, anchor=self._m1_0x3ctranslator30000x3e__arrow_rotate_point, rotate_pad=False, transform_anchor=True)
            arrow_rend = renpy.render(arrow, width, height, st, at)
            placement = builtins.list(arrow.get_placement())
            placement[:2] = x, y
            pos = self._place_func(w, h, arrow_rend.width, arrow_rend.height, placement)
            result.blit(arrow_rend, pos)
            if self.focusable:
                mask = self.style.focus_mask
                if mask is True:
                    mask = back_rend
                elif callable(mask):
                    pass
                elif mask is not None:
                    mask = renpy.render(mask, width, height, st, at)
                if mask is None:
                    fmx = None
                    fmy = None
                else:
                    fmx = 0
                    fmy = 0
                result.add_focus(self, None, 0, 0, w, h, fmx, fmy, mask)
            return result


    class MessageHandler(SingleTone):
        __author__ = u'Vladya'
        URL = u'https://api.vladya.net/messages.json'
        UPDATE_TIME = 600.0

        def __init__(self, gui_object):
            if self.initialized:
                return
            self._m1_0x3ctranslator30000x3e__gui_object = gui_object
            self._m1_0x3ctranslator30000x3e__show = False
            self._m1_0x3ctranslator30000x3e__last_check = None
            self.initialized = True

        def _periodic_callback(self):
            if self._m1_0x3ctranslator30000x3e__last_check is None:
                self._update()
            elif time.time() - self._m1_0x3ctranslator30000x3e__last_check >= self.UPDATE_TIME:
                self._update()

        def _update(self):
            try:
                _response = store._translator3000.current_session.get(self.URL, _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
                _messaged_data = _response.json()
            except Exception as ex:
                store._translator3000.LOGGER.exception(ex)
                new_messages = builtins.list()
                deleted_ids = builtins.list()
            else:
                new_messages = _messaged_data[u'messages']
                deleted_ids = _messaged_data[u'deleted_ids']
            for msg in new_messages:
                message_id = unicode(msg[u'message_id'])
                readed = False
                if message_id in self.persistent[u'messages']:
                    readed = self.persistent[u'messages'][message_id][u'readed']
                self.persistent[u'messages'][message_id] = msg
                self.persistent[u'messages'][message_id][u'message_id'] = message_id
                self.persistent[u'messages'][message_id][u'readed'] = readed
            for del_id in builtins.map(unicode, deleted_ids):
                self.persistent[u'messages'].pop(del_id, None)
            self.translator_object._multi_persistent.save()
            self._m1_0x3ctranslator30000x3e__last_check = time.time()

        @property
        def show(self):
            return self._m1_0x3ctranslator30000x3e__show

        @show.setter
        def show(self, new_value):
            self._m1_0x3ctranslator30000x3e__show = bool(new_value)

        @property
        def gui_object(self):
            return self._m1_0x3ctranslator30000x3e__gui_object

        @property
        def translator_object(self):
            return self.gui_object._translator

        @property
        def persistent(self):
            if self.translator_object._multi_persistent.messages_data is None:
                self.translator_object._multi_persistent.messages_data = builtins.dict()
                self.translator_object._multi_persistent.messages_data[u'messages'] = builtins.dict()
                self.translator_object._multi_persistent.save()
            return self.translator_object._multi_persistent.messages_data

        def is_have_unread(self):
            for message in self.persistent[u'messages'].values():
                if not message[u'readed']:
                    return True
            return False

        def mark_as_read(self, message_id):
            self.persistent[u'messages'][message_id][u'readed'] = True
            self.translator_object._multi_persistent.save()

        def mark_all_as_read(self):
            for message in self.persistent[u'messages'].values():
                message[u'readed'] = True
            self.translator_object._multi_persistent.save()

        def get_messages(self, update=False):
            if update:
                self._update()
            for message in builtins.sorted(self.persistent[u'messages'].values(), key=lambda x: x[u'message_id'], reverse=True):
                if not message[u'message']:
                    continue
                message_text = None
                for lng in (self.gui_object.gui_language, u'english', u'russian', tuple(builtins.sorted(tuple(message[u'message'].keys())))[0]):
                    if lng in message[u'message']:
                        message_text = message[u'message'][lng]
                        break
                else:
                    raise RuntimeError(message)
                yield message[u'message_id'], message_text, message[u'readed']


    class PopupWindowsHandler(SingleTone):
        __author__ = u'Vladya'
        MB_ABORTRETRYIGNORE = 2
        MB_CANCELTRYCONTINUE = 6
        MB_HELP = 16384
        MB_OK = 0
        MB_OKCANCEL = 1
        MB_RETRYCANCEL = 5
        MB_YESNO = 4
        MB_YESNOCANCEL = 3
        MB_ICONEXCLAMATION = 48
        MB_ICONWARNING = 48
        MB_ICONINFORMATION = 64
        MB_ICONASTERISK = 64
        MB_ICONQUESTION = 32
        MB_ICONSTOP = 16
        MB_ICONERROR = 16
        MB_ICONHAND = 16
        MB_DEFBUTTON1 = 0
        MB_DEFBUTTON2 = 256
        MB_DEFBUTTON3 = 512
        MB_DEFBUTTON4 = 768
        MB_APPLMODAL = 0
        MB_SYSTEMMODAL = 4096
        MB_TASKMODAL = 8192
        MB_DEFAULT_DESKTOP_ONLY = 131072
        MB_RIGHT = 524288
        MB_RTLREADING = 1048576
        MB_SETFOREGROUND = 65536
        MB_TOPMOST = 262144
        MB_SERVICE_NOTIFICATION = 2097152
        RETURN_VALUES = __renpy__dict__({3: u'IDABORT', 2: u'IDCANCEL', 11: u'IDCONTINUE', 5: u'IDIGNORE', 7: u'IDNO', 1: u'IDOK', 4: u'IDRETRY', 10: u'IDTRYAGAIN', 6: u'IDYES'})
        SHOW_TIMES_BEFORE_HIDE_NOTIFY = 5

        def __init__(self, translator):
            if self.initialized:
                return
            self._m1_0x3ctranslator30000x3e__translator = translator
            self._m1_0x3ctranslator30000x3e__lock = threading.RLock()
            self.initialized = True

        @property
        def popup_windows_status(self):
            with self._m1_0x3ctranslator30000x3e__lock:
                if self._m1_0x3ctranslator30000x3e__translator._multi_persistent.popup_windows_status is None:
                    self._m1_0x3ctranslator30000x3e__translator._multi_persistent.popup_windows_status = builtins.dict()
                    self._m1_0x3ctranslator30000x3e__translator._multi_persistent.save()
                return self._m1_0x3ctranslator30000x3e__translator._multi_persistent.popup_windows_status

        def _reset_stats(self):
            with self._m1_0x3ctranslator30000x3e__lock:
                self.popup_windows_status.clear()
                self._m1_0x3ctranslator30000x3e__translator._multi_persistent.save()

        def _show_window(self, text, title, flags=None, _raise=False, **format_kw):
            if not renpy.windows:
                return None
            action_kw, other_kw, format_kw = renpy.split_properties(format_kw, u'action_', u'other_', u'')
            _count = other_kw.pop(u'count', True)
            with self._m1_0x3ctranslator30000x3e__lock:
                _k = u'|'.join((title.format(**format_kw), text.format(**format_kw)))
                if _k not in self.popup_windows_status:
                    self.popup_windows_status[_k] = 0
                    self._m1_0x3ctranslator30000x3e__translator._multi_persistent.save()
                if self.popup_windows_status[_k] is False:
                    return None
            if flags is None:
                flags = self.MB_OK
            text = self._m1_0x3ctranslator30000x3e__translator._gui.translate(text, not_translate_mark=False).format(**format_kw)
            title = self._m1_0x3ctranslator30000x3e__translator._gui.translate(title, not_translate_mark=False).format(**format_kw)
            try:
                result = ctypes.windll.user32.MessageBoxW(None, text, title, flags)
                if result not in self.RETURN_VALUES:
                    error_code = ctypes.get_last_error()
                    raise ctypes.WinError(error_code)
            except Exception as ex:
                if _raise:
                    raise
                store._translator3000.LOGGER.exception(ex)
                return None
            return_value = self.RETURN_VALUES[result]
            if return_value in action_kw:
                _action = action_kw[return_value]
                renpy.run(_action)
            with self._m1_0x3ctranslator30000x3e__lock:
                if self.popup_windows_status[_k] is not True:
                    if self.popup_windows_status[_k] is not False:
                        if _count:
                            self.popup_windows_status[_k] += 1
                            self._m1_0x3ctranslator30000x3e__translator._multi_persistent.save()
                        if self.popup_windows_status[_k] > self.SHOW_TIMES_BEFORE_HIDE_NOTIFY:
                            _ret = self._show_window(u'\u0414\u0435\u043c\u043e\u043d\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u044d\u0442\u043e \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u0432 \u0434\u0430\u043b\u044c\u043d\u0435\u0439\u0448\u0435\u043c?', title, flags=self.MB_ICONQUESTION | self.MB_YESNO, _raise=False, other_count=False)
                            if _ret == u'IDYES':
                                self.popup_windows_status[_k] = True
                            elif _ret == u'IDNO':
                                self.popup_windows_status[_k] = False
                            self._m1_0x3ctranslator30000x3e__translator._multi_persistent.save()
            return return_value

        def show_window(self, text, title, flags=None, _raise=False, create_thread=True, **format_kw):
            _callable = renpy.partial(self._show_window, text=text, title=title, flags=flags, _raise=_raise, **format_kw)
            if not create_thread:
                return _callable()
            th = threading.Thread(target=_callable)
            th.daemon = True
            th.start()

        def show_info(self, text, title, flags=None, _raise=False, create_thread=True, **format_kw):
            _flags = self.MB_OK
            _flags |= self.MB_ICONINFORMATION
            if flags is not None:
                _flags |= flags
            return self.show_window(text, title, _flags, _raise, create_thread, **format_kw)

        def show_warning(self, text, title, flags=None, _raise=False, create_thread=True, **format_kw):
            _flags = self.MB_OK
            _flags |= self.MB_ICONWARNING
            if flags is not None:
                _flags |= flags
            return self.show_window(text, title, _flags, _raise, create_thread, **format_kw)

        def show_error(self, text, title, flags=None, _raise=False, create_thread=True, **format_kw):
            _flags = self.MB_OK
            _flags |= self.MB_ICONERROR
            if flags is not None:
                _flags |= flags
            return self.show_window(text, title, _flags, _raise, create_thread, **format_kw)


    class TooltipHandler(SingleTone):
        __author__ = u'Vladya'
        TOOLTIPS = builtins.dict(arrow_up_button=u'\u041f\u0440\u043e\u043a\u0440\u0443\u0442\u043a\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b \u0432\u0432\u0435\u0440\u0445', vbar_element=u'\u041f\u0440\u043e\u043a\u0440\u0443\u0442\u043a\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b', arrow_down_button=u'\u041f\u0440\u043e\u043a\u0440\u0443\u0442\u043a\u0430 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b \u0432\u043d\u0438\u0437', close_window_button=u'\u0417\u0430\u043a\u0440\u044b\u0442\u044c \u043e\u043a\u043d\u043e', back_button=u'\u041d\u0430\u0437\u0430\u0434', docs_button=u'\u0421\u043f\u0440\u0430\u0432\u043a\u0430\n\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0441\u043f\u0440\u0430\u0432\u043a\u0443', dark_theme_button=u'\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0446\u0432\u0435\u0442\u043e\u0432\u0443\u044e \u0442\u0435\u043c\u0443', refresh_button=u'\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0443', choice_lang=u'\u041f\u043e\u043c\u0435\u043d\u044f\u0442\u044c \u044f\u0437\u044b\u043a \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0430', messages_button=u'\u041b\u0435\u043d\u0442\u0430 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0439 \u043e\u0442 \u043a\u043e\u043c\u0430\u043d\u0434\u044b Translator3000', alpha_bar_element=u'\u0420\u0435\u0433\u0443\u043b\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u0440\u043e\u0437\u0440\u0430\u0447\u043d\u043e\u0441\u0442\u0438 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0433\u043e \u043e\u043a\u043d\u0430', zoom_bar_element=u'\u041c\u0430\u0441\u0448\u0442\u0430\u0431 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0433\u043e \u043e\u043a\u043d\u0430', zoom_plus_button=u'\u0423\u0432\u0435\u043b\u0438\u0447\u0438\u0442\u044c \u043c\u0430\u0441\u0448\u0442\u0430\u0431 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0433\u043e \u043e\u043a\u043d\u0430 (\u0442\u0430\u043a \u0436\u0435 "ctrl +")', zoom_minus_button=u'\u0423\u043c\u0435\u043d\u044c\u0448\u0438\u0442\u044c \u043c\u0430\u0441\u0448\u0442\u0430\u0431 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0433\u043e \u043e\u043a\u043d\u0430 (\u0442\u0430\u043a \u0436\u0435 "ctrl -")', off_mode_button=u'\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0447\u0438\u043a', prescan_mode_button=u'\u0420\u0435\u0436\u0438\u043c \u043f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f', db_only_mode_button=u'\u0420\u0435\u0436\u0438\u043c \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0430 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u044e\u0449\u0438\u0439 \u0442\u043e\u043b\u044c\u043a\u043e \u0438\u043c\u0435\u044e\u0449\u0443\u044e\u0441\u044f \u0431\u0430\u0437\u0443 \u0434\u0430\u043d\u043d\u044b\u0445 (\u0431\u0435\u0437 \u0441\u0435\u0442\u0435\u0432\u044b\u0445 \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432)', realtime_mode_button=u'\u0420\u0435\u0436\u0438\u043c \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0430 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u044e\u0449\u0438\u0439 \u0438\u043c\u0435\u044e\u0449\u0443\u044e\u0441\u044f \u0431\u0430\u0437\u0443 \u0434\u0430\u043d\u043d\u044b\u0445 \u0438 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u044f\u0449\u0438\u0439 \u0441\u0435\u0442\u0435\u0432\u044b\u0435 \u0437\u0430\u043f\u0440\u043e\u0441\u044b \u0434\u043b\u044f \u043d\u0435\u043f\u0435\u0440\u0435\u0432\u0435\u0434\u0451\u043d\u043d\u043e\u0433\u043e \u0440\u0430\u043d\u0435\u0435 \u0442\u0435\u043a\u0441\u0442\u0430', minimize_button=u'\u0421\u0432\u0435\u0440\u043d\u0443\u0442\u044c', maximize_button=u'\u0420\u0430\u0437\u0432\u0435\u0440\u043d\u0443\u0442\u044c', text_size_minus_button=u'\u0423\u043c\u0435\u043d\u044c\u0448\u0438\u0442\u044c \u0440\u0430\u0437\u043c\u0435\u0440 \u0442\u0435\u043a\u0441\u0442\u0430', text_size_plus_button=u'\u0423\u0432\u0435\u043b\u0438\u0447\u0438\u0442\u044c \u0440\u0430\u0437\u043c\u0435\u0440 \u0442\u0435\u043a\u0441\u0442\u0430', yes_button=u'\u0414\u0410\u0410\u0410\u0410\u0410\u0410!', no_button=u'\u041d\u0435\u0435\u0435\u0435\u0435...', auto_load_font_button=u'\u0428\u0440\u0438\u0444\u0442 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0441\u044f \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0432 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u0438 \u0441 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u043c \u044f\u0437\u044b\u043a\u043e\u043c \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0430')
        MOUSE_OFFSET = 0, 30

        def __init__(self, gui_object):
            if self.initialized:
                return
            self._m1_0x3ctranslator30000x3e__gui_object = gui_object
            self._m1_0x3ctranslator30000x3e__tooltip = store.Tooltip(None)
            self.initialized = True

        @property
        def tt(self):
            return self._m1_0x3ctranslator30000x3e__tooltip

        @property
        def tt_text(self):
            if self.tt.value is None:
                return self._m1_0x3ctranslator30000x3e__gui_object.translate(u'...')
            return self._m1_0x3ctranslator30000x3e__gui_object.translate(self.tt.value)

        def DismissAction(self):
            return self.tt.Action(None)

        def Action(self, tt_id):
            return self.tt.Action(self.TOOLTIPS.get(tt_id, tt_id))

        @staticmethod
        def _tr3000_get_mouse_pos():
            result = renpy.get_mouse_pos()
            if not result:
                return (0, 0)
            return tuple(builtins.map(int, result))

        def _hide(self, *args, **kwargs):
            renpy.run(self.DismissAction())
            return None

        @classmethod
        def _set_pos_and_zoom(cls, trans, st, at):
            if not renpy.display.draw:
                return 0.0
            screen_w, screen_h = builtins.map(int, (store.config.screen_width, store.config.screen_height))
            w, h = builtins.map(int, renpy.render(trans.child, screen_w, screen_h, st, at).get_size())
            x, y = cls._tr3000_get_mouse_pos()
            xoffset, yoffset = builtins.map(int, cls.MOUSE_OFFSET)
            x += xoffset
            y += yoffset
            x_end = x + w
            y_end = y + h
            if x_end > screen_w:
                x -= x_end - screen_w
            if y_end > screen_h:
                y -= y_end - screen_h
            trans.pos = x, y
            trans.zoom = persistent.tr3000_zoom_main_window
            return 0.0


    class ChoiceMenuHandler(SingleTone):
        __author__ = u'Vladya'
        LOGGER = None
        ITEMS_BACKUP = builtins.dict()
        ENTRIES_BACKUP = builtins.dict()
        CHAINS_CACHE = builtins.dict()

        def __init__(self, gui_object):
            self._m1_0x3ctranslator30000x3e__gui_object = gui_object

        @staticmethod
        def _generate_ast(_txt, _fn=None):
            if not _txt.strip():
                return __renpy__list__([])
            if not _fn:
                _fn = u'<dynamic_ast>'
            stmts = renpy.parser.parse(_fn, _txt)
            if stmts is None:
                raise RuntimeError(u'\n\n'.join(renpy.parser.get_parse_errors()))
            renpy.game.script.assign_names(stmts, _fn)
            return stmts

        @classmethod
        def get_chain_for_current_node(cls):
            current_node_id = renpy.game.context().current
            if not current_node_id:
                return ()
            if current_node_id not in cls.CHAINS_CACHE:
                return ()
            return cls.CHAINS_CACHE[current_node_id]

        @staticmethod
        def _get_pycode_strings(code_string):
            code_strings = builtins.list(filter(lambda x: x.strip(), map(lambda x: re.sub(u'\\s', u' ', x).rstrip(), re.split(u'[\\r\\n]+', code_string))))
            spaces = re.search(u'^\\s+', code_strings[0])
            if spaces:
                slice_start = len(spaces.group())
                code_strings = map(lambda x: x[slice_start:], code_strings)
            return tuple(code_strings)

        def parse_block(self, block, _indent=False, add_fill=False):
            result = builtins.list()
            for _sub_node in block:
                if isinstance(_sub_node, (renpy.ast.Python, renpy.ast.EarlyPython)):
                    try:
                        result.extend(self._get_pycode_strings(_sub_node.code.source))
                    except Exception as ex:
                        self.LOGGER.exception(ex)
                elif isinstance(_sub_node, renpy.ast.Call):
                    code_string = u'call '
                    if _sub_node.expression:
                        code_string += u'expression "{0}"'.format(_sub_node.label)
                    else:
                        code_string += _sub_node.label
                    result.append(code_string)
                elif isinstance(_sub_node, renpy.ast.Return):
                    break
                elif isinstance(_sub_node, renpy.ast.Menu):
                    result.append(u'menu: ...')
                elif isinstance(_sub_node, renpy.ast.Jump):
                    code_string = u'jump '
                    if _sub_node.expression:
                        code_string += u'expression "{0}"'.format(_sub_node.target)
                    else:
                        code_string += _sub_node.target
                    result.append(code_string)
                elif isinstance(_sub_node, renpy.ast.While):
                    result.append(u'while {0}:'.format(_sub_node.condition))
                    result.extend(self.parse_block(_sub_node.block, True, True))
                elif isinstance(_sub_node, renpy.ast.If):
                    last_i = len(_sub_node.entries) - 1
                    for i, (_condition, block) in enumerate(_sub_node.entries):
                        if i == 0:
                            result.append(u'if {0}:'.format(_condition))
                        elif i == last_i and _condition == u'True':
                            result.append(u'else:')
                        else:
                            result.append(u'elif {0}:'.format(_condition))
                        result.extend(self.parse_block(block, True, True))
            if add_fill and not result:
                result.append(self._m1_0x3ctranslator30000x3e__gui_object.translate(u'# \u041d\u0435\u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u043a\u043e\u0434', not_translate_mark=False))
            if _indent:
                for i, val in enumerate(result[:]):
                    result[i] = u''.join((u'    ', val))
            return tuple(result)

        def get_py_code(self, block, size_limit=15):
            if not block:
                return ()
            result = tuple(filter(lambda x: x.strip(), map(lambda x: x.rstrip(), self.parse_block(block))))
            if len(result) >= size_limit:
                result = result[:size_limit - 1] + (u'...',)
            return result

        def get_current_menu(self, get_only_visible_labels=False):
            if renpy.predicting():
                return ()
            current_node_id = renpy.game.context().current
            if not current_node_id:
                return ()
            if current_node_id not in self.ITEMS_BACKUP:
                return ()
            result = builtins.list()
            current_items = self.ITEMS_BACKUP[current_node_id]
            for _label, _condition, block in current_items:
                try:
                    condition = renpy.python.py_eval(_condition)
                except Exception as ex:
                    self.LOGGER.exception(ex)
                    condition = True
                if get_only_visible_labels:
                    if condition:
                        result.append(_label)
                    continue
                py_code = self.get_py_code(block)
                result.append((_label, _condition, condition, py_code))
            return tuple(result)

        def get_last_py_code(self):
            if renpy.predicting():
                return ()
            chain = self.get_chain_for_current_node()
            return self.get_py_code(chain)

        def prepare_init(self, _deep=10):
            ChoiceMenuHandler.LOGGER = store._translator3000.LOGGER.getChild(u'MenuExpander')
            ChoiceMenuHandler.LOGGER.debug('Initializing. Stage 1.')
            node_prev_mapping = builtins.dict()
            for node in renpy.game.script.namemap.values():
                try:
                    _scry = node.scry()
                except Exception as ex:
                    ChoiceMenuHandler.LOGGER.exception(ex)
                    _next_node = None
                else:
                    if hasattr(_scry, u'_next') and _scry._next:
                        _next_node = _scry._next
                    else:
                        _next_node = None
                if _next_node and hasattr(_next_node, u'name'):
                    if _next_node.name not in node_prev_mapping:
                        node_prev_mapping[_next_node.name] = builtins.list()
                    if node not in node_prev_mapping[_next_node.name]:
                        node_prev_mapping[_next_node.name].append(node)
            ChoiceMenuHandler.LOGGER.debug('Initializing. Stage 2.')
            ChoiceMenuHandler.CHAINS_CACHE = builtins.dict()
            ChoiceMenuHandler.ITEMS_BACKUP = builtins.dict()
            ChoiceMenuHandler.ENTRIES_BACKUP = builtins.dict()
            for node in renpy.game.script.namemap.values():
                if os.getenv(u'RENPY_TRANSLATOR3000_COMPILE', u'0') == u'1':
                    continue
                if not hasattr(node, u'name'):
                    continue
                if not hasattr(node, u'filename'):
                    continue
                if node.filename.startswith(u'game/tl/'):
                    continue
                if node.filename.startswith(u'renpy/'):
                    continue
                if isinstance(node, renpy.ast.Menu):
                    if hasattr(node, u'items'):
                        ChoiceMenuHandler.ITEMS_BACKUP[node.name] = node.items[:]
                elif isinstance(node, renpy.ast.If):
                    if hasattr(node, u'entries'):
                        ChoiceMenuHandler.ENTRIES_BACKUP[node.name] = node.entries[:]
                result = builtins.list((node,))
                while True:
                    if len(result) >= _deep:
                        break
                    if not hasattr(result[-1], u'name'):
                        break
                    if result[-1].name not in node_prev_mapping:
                        break
                    prevs = node_prev_mapping[result[-1].name]
                    if len(prevs) != 1:
                        break
                    result.append(prevs[0])
                ChoiceMenuHandler.CHAINS_CACHE[node.name] = tuple(result[::-1])
            ChoiceMenuHandler.LOGGER.debug('Initializing is done')

        def update_all_menu(self, enable=True):
            ChoiceMenuHandler.LOGGER.debug('Start menu updating')
            for key, node in renpy.game.script.namemap.items():
                if isinstance(node, renpy.ast.Menu):
                    if key in ChoiceMenuHandler.ITEMS_BACKUP:
                        items = ChoiceMenuHandler.ITEMS_BACKUP[key][:]
                        if enable:
                            node.items = builtins.list(map(lambda it: (it[0], u'True', it[2]), items))
                        else:
                            node.items = items
                elif isinstance(node, renpy.ast.If):
                    if key in ChoiceMenuHandler.ENTRIES_BACKUP:
                        entries = ChoiceMenuHandler.ENTRIES_BACKUP[key][:]
                        if enable:
                            node.entries = builtins.list(((u'True', builtins.list((self._get_menu_from_if(node, entries),))),))
                        else:
                            node.entries = entries
                else:
                    continue
            ChoiceMenuHandler.LOGGER.debug('Done')

        def _get_menu_from_if(self, if_node, orig_entries):
            asts = self._generate_ast(u'''menu:
    "Placeholder":
        pass''', u'<menu_from_{0}>'.format(id(if_node)))
            if asts and isinstance(asts[0], renpy.ast.Menu):
                menu_node = asts[0]
            else:
                return None
            menu_node.next = if_node.next
            asts = self._generate_ast(u'if True:\n    pass', u'<if_from_{0}>'.format(id(if_node)))
            if asts and isinstance(asts[0], renpy.ast.If):
                new_if_node = asts[0]
            else:
                return None
            new_if_node.entries = orig_entries
            new_if_node.next = if_node.next
            items = builtins.list()
            _max_i = len(orig_entries) - 1
            for i, (_condition, block) in enumerate(orig_entries):
                if _condition == u'True' and i == _max_i:
                    _label = self._m1_0x3ctranslator30000x3e__gui_object.translate(u'\u0418\u043d\u0430\u0447\u0435:\n', not_translate_mark=False)
                else:
                    for keyword, kw_translate in ((u'True', u'\u0418\u0441\u0442\u0438\u043d\u0430'), (u'False', u'\u041b\u043e\u0436\u044c'), (u'None', u'\u041d\u0438\u0447\u0442\u043e'), (u'is not', u'\u043d\u0435 \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f'), (u'is', u'\u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f'), (u'not', u'\u043d\u0435')):
                        _condition = re.sub(u'(\\W|^)({0})(\\W|$)'.format(keyword), u'\\1{0}\\3'.format(self._m1_0x3ctranslator30000x3e__gui_object.translate(kw_translate, not_translate_mark=False)), _condition)
                    _label = self._m1_0x3ctranslator30000x3e__gui_object.translate(u'\u0415\u0441\u043b\u0438 {0}:\n', not_translate_mark=False).format(_condition)
                _label += u'\n'.join(filter(lambda x: x.strip(), map(lambda x: x.rstrip(), self.parse_block(block, True, True))))
                items.append((u'###notTranslate######forceTags###{0}'.format(_label), u'True', block))
            _label = u'###notTranslate######forceTags###{0}'.format(self._m1_0x3ctranslator30000x3e__gui_object.translate(u'\u041f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e (\u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0439 \u043f\u0443\u0442\u044c)', not_translate_mark=False))
            items.append((_label, u'True', builtins.list((new_if_node,))))
            menu_node.items = items
            if hasattr(menu_node, u'item_arguments'):
                menu_node.item_arguments = None
            return menu_node


































































































































































































































































































init -40 python in _translator3000_gui:
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins
    try:
        import renpy.pygame as pygame
    except ImportError:
        import pygame_sdl2 as pygame
    import os
    import re
    import time
    import ctypes
    import posixpath
    import collections
    import math
    import hashlib
    import copy
    import sys
    import threading
    import store
    import _translator3000
    from os import path
    from store import persistent, im, style
    if store.translator3000_preload.PY3:
        unicode = builtins.str
        basestring = builtins.str, builtins.bytes
        xrange = builtins.range
        unichr = builtins.chr
        long = builtins.int
    else:
        unicode = builtins.unicode
        basestring = builtins.basestring
        xrange = builtins.xrange
        unichr = builtins.unichr
        long = builtins.long
    PHI_CONST = 0.6180339887498949
    PHI_CONST, PHI_CONST2 = 1.0 - PHI_CONST, PHI_CONST
    PHI_CONST3 = 1.0 / PHI_CONST2
    SingleTone = store.translator3000_preinit.SingleTone

    def resize_from_1080(value_1080, minimum=None):
        assert isinstance(value_1080, (int, long, float)), value_1080
        if minimum is not None:
            assert builtins.type(value_1080) is builtins.type(minimum)
        coef = min(float(store.config.screen_width) / 1920.0, float(store.config.screen_height) / 1080.0)
        value = float(value_1080) * coef
        if not isinstance(value_1080, float):
            ValueClass = builtins.type(value_1080)
            value = ValueClass(builtins.round(value))
        if minimum is not None and value < minimum:
            return minimum
        return value











init 2:
    screen translator3000_mini_window(**kwargs):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        window:
            if "window_sub_style" in kwargs:
                style style.translator3000_window[kwargs["window_sub_style"]]
            hbox:
                align (.0, .5)
                box_reverse True
                first_spacing None
                spacing _translator3000_gui.resize_from_1080(20, 1)
                $ _cols = kwargs.get("cols", 1)
                if _cols > 1:
                    vpgrid id "tr3000_main_vpg":
                        cols _cols
                        xsize _translator3000.builtins.max(_translator3000.builtins.min((.17 * float(_cols)), 1.), .0)
                        spacing kwargs.get("spacing", _translator3000_gui.resize_from_1080(10, 1))
                        yinitial .0
                        mousewheel True
                        pagekeys True
                        transclude
                else:
                    viewport id "tr3000_main_vpg":
                        yinitial .0
                        xsize .35
                        mousewheel True
                        pagekeys True
                        has vbox
                        first_spacing kwargs.get("first_spacing", _translator3000_gui.resize_from_1080(5, 1))
                        spacing kwargs.get("spacing", _translator3000_gui.resize_from_1080(3, 1))
                        box_reverse kwargs.get("box_reverse", False)
                        transclude
                vbox:
                    first_spacing None
                    spacing _translator3000_gui.resize_from_1080(5, 1)
                    yalign .5
                    null height _translator3000_gui.resize_from_1080(5, 1)
                    imagebutton:
                        xalign .5
                        background _translator3000_gui.theme.buttonBack
                        hover_background _translator3000_gui.theme.buttonBackHover
                        idle _translator3000_gui.theme.arrowUp
                        hover _translator3000_gui.theme.arrowUpHover
                        action Scroll("tr3000_main_vpg", "vertical decrease")
                        hovered translator3000._gui._tooltip_handler.Action("arrow_up_button")
                    vbar:
                        style "translator3000_vbar"
                        ymaximum .965
                        xalign .5
                        value YScrollValue("tr3000_main_vpg")
                        hovered translator3000._gui._tooltip_handler.Action("vbar_element")
                    imagebutton:
                        xalign .5
                        background _translator3000_gui.theme.buttonBack
                        hover_background _translator3000_gui.theme.buttonBackHover
                        idle _translator3000_gui.theme.arrowDown
                        hover _translator3000_gui.theme.arrowDownHover
                        action Scroll("tr3000_main_vpg", "vertical increase")
                        hovered translator3000._gui._tooltip_handler.Action("arrow_down_button")
                    null height _translator3000_gui.resize_from_1080(5, 1)
    screen translator3000_base_vbox_in_window(*_actions, **kwargs):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        showif translator3000._gui.show:
            if renpy.context()._menu:
                key "game_menu" action (
                    (_actions + (translator3000._gui.BackAction(), ))
                )
            window:
                at translator3000_general_window(persistent.tr3000_alpha_main_window, persistent.tr3000_zoom_main_window)
                has vbox
                window:
                    background _translator3000_gui.theme.top_panel_background
                    xfill True
                    has hbox
                    xfill True
                    hbox:
                        align (.03, .5)
                        add _translator3000_gui.theme.mainMark
                        text "{#notTranslate}Translator3000":
                            yalign .5
                    hbox:
                        align (.97, .5)
                        spacing _translator3000_gui.resize_from_1080(20, 2)
                        imagebutton:
                            yalign .5
                            background _translator3000_gui.theme.buttonBack
                            hover_background _translator3000_gui.theme.buttonBackHover
                            if translator3000._gui._current_menu_stack:
                                idle _translator3000_gui.theme.closeButtonElement
                                hover _translator3000_gui.theme.closeButtonElementHover
                                hovered translator3000._gui._tooltip_handler.Action("back_button")
                            elif translator3000._setting["useMinimizeButton"]:
                                idle _translator3000_gui.theme.closeButtonElement
                                hover _translator3000_gui.theme.closeButtonElementHover
                                hovered translator3000._gui._tooltip_handler.Action("minimize_button")
                            else:
                                idle _translator3000_gui.theme.closeButtonElement
                                hover _translator3000_gui.theme.closeButtonElementHover
                                hovered translator3000._gui._tooltip_handler.Action("close_window_button")
                            action (_actions + (translator3000._gui.BackAction(), ))
                hbox:
                    xfill True
                    align (.0, .5)
                    hbox:
                        align (.03, .5)
                        imagebutton:
                            idle _translator3000_gui.theme.mainMenuBack
                            hover _translator3000_gui.theme.mainMenuBackHover
                            action (_actions + (translator3000._gui.BackAction(), ))
                            hovered translator3000._gui._tooltip_handler.Action("back_button")
                        imagebutton:
                            idle _translator3000_gui.theme.mainMenuDocs
                            hover _translator3000_gui.theme.mainMenuDocsHover
                            action OpenURL("https://translator3000.vladya.net/?utm_source=translator3000_app")
                            hovered translator3000._gui._tooltip_handler.Action("docs_button")
                        null width _translator3000_gui.resize_from_1080(5, 1)
                        imagebutton:
                            idle _translator3000_gui.theme.themeSwitcher
                            hover _translator3000_gui.theme.themeSwitcherHover
                            action _translator3000_gui.theme.ToggleTheme()
                            hovered translator3000._gui._tooltip_handler.Action("dark_theme_button")
                        null width _translator3000_gui.resize_from_1080(5, 1)
                        imagebutton:
                            idle _translator3000_gui.theme.refreshPage
                            hover _translator3000_gui.theme.refreshPageHover
                            action (_translator3000.Translator3000.NeedRestartAction(), Function(translator3000.vars_changer.clear_cache))
                            hovered translator3000._gui._tooltip_handler.Action("refresh_button")
                    hbox:
                        align (.95, .5)
                        window:
                            align (.5, .5)
                            xsize _translator3000_gui.resize_from_1080(60, 1)
                            ysize _translator3000_gui.resize_from_1080(60, 1)
                            textbutton "{{#notTranslate}}{0}".format(translator3000._gui.gui_language[:2].upper()):
                                align (.5, .5)
                                background None
                                text_size _translator3000_gui.resize_from_1080(40, 1)
                                text_bold True
                                action CycleField(translator3000._gui, "gui_language", tuple(sorted(translator3000._gui.available_languages)))
                                hovered translator3000._gui._tooltip_handler.Action("choice_lang")
                        window:
                            align (.5, .5)
                            xsize _translator3000_gui.resize_from_1080(60, 1)
                            ysize _translator3000_gui.resize_from_1080(60, 1)
                            has imagebutton
                            align (.5, .5)
                            if translator3000._gui._message_handler.is_have_unread():
                                idle _translator3000_gui.theme.messageActive
                                hover _translator3000_gui.theme.messageActiveHover
                            else:
                                idle _translator3000_gui.theme.messagePassive
                                hover _translator3000_gui.theme.messagePassiveHover
                            action ToggleField(translator3000._gui._message_handler, "show")
                            hovered translator3000._gui._tooltip_handler.Action("messages_button")
                        window:
                            align (.5, .5)
                            xsize _translator3000_gui.resize_from_1080(90, 1)
                            ysize _translator3000_gui.resize_from_1080(60, 1)
                            add _translator3000_gui.ClockBar(
                                    _translator3000_gui.theme.clockBarBack1,
                                    _translator3000_gui.theme.clockBarArrow1,
                                    (.5, .81),
                                    (.35, .78),
                                    (-100, 100),
                                    value=FieldValue(
                                        persistent,
                                        "tr3000_alpha_main_window",
                                        range=.95,
                                        offset=.05,
                                        step=.01
                                    ),
                                    hovered=translator3000._gui._tooltip_handler.Action("alpha_bar_element"),
                                    align=(.5, .5)
                                )
                        window:
                            align (.5, .5)
                            xsize _translator3000_gui.resize_from_1080(120, 1)
                            ysize _translator3000_gui.resize_from_1080(60, 1)
                            has hbox
                            align (.5, .5)
                            add _translator3000_gui.ClockBar(
                                        _translator3000_gui.theme.clockBarBack1,
                                        _translator3000_gui.theme.clockBarArrow1,
                                        (.5, .81),
                                        (.35, .78),
                                        (-100, 100),
                                        value=StaticValue((persistent.tr3000_zoom_main_window - _translator3000_gui.PHI_CONST), range=(1. - _translator3000_gui.PHI_CONST)),
                                        hovered=translator3000._gui._tooltip_handler.Action("zoom_bar_element")
                                    )
                            vbox:
                                yalign .5
                                first_spacing None
                                spacing 0
                                imagebutton:
                                    idle _translator3000_gui.theme.zoomPlus
                                    hover _translator3000_gui.theme.zoomPlusHover
                                    keysym ("ctrl_K_EQUALS", "ctrl_K_KP_PLUS")
                                    action (
                                                SensitiveIf((persistent.tr3000_zoom_main_window < 1.)),
                                                SetField(persistent, "tr3000_zoom_main_window", _translator3000.builtins.min((persistent.tr3000_zoom_main_window + .05), 1.))
                                            )
                                    alternate SetField(persistent, "tr3000_zoom_main_window", _translator3000_gui.PHI_CONST2)
                                    hovered translator3000._gui._tooltip_handler.Action("zoom_plus_button")
                                imagebutton:
                                    idle _translator3000_gui.theme.zoomMinus
                                    hover _translator3000_gui.theme.zoomMinusHover
                                    keysym ("ctrl_K_MINUS", "ctrl_K_KP_MINUS")
                                    action (
                                                SensitiveIf((persistent.tr3000_zoom_main_window > _translator3000_gui.PHI_CONST)),
                                                SetField(persistent, "tr3000_zoom_main_window", _translator3000.builtins.max((persistent.tr3000_zoom_main_window - .05), _translator3000_gui.PHI_CONST))
                                            )
                                    alternate SetField(persistent, "tr3000_zoom_main_window", _translator3000_gui.PHI_CONST)
                                    hovered translator3000._gui._tooltip_handler.Action("zoom_minus_button")
                window:
                    background _translator3000_gui.theme.main_window_background
                    has hbox
                    if kwargs.get("use_mini_window", True):
                        use translator3000_mini_window(**kwargs):
                            transclude
                    else:
                        window:
                            align (.0, .5)
                            transclude
                    window:
                        background _translator3000_gui.theme.right_side_background
                        align (1., .0)
                        xfill True
                        yfill True
                        has vbox
                        window:
                            background _translator3000_gui.theme.modes_right_panel_background
                            yalign .0
                            has hbox
                            xfill True
                            for _name, _mode, doc_url, tooltip_id in (
                                        ("Откл", "off", "https://translator3000.vladya.net/gui.html?utm_source=translator3000_app#work-modes", "off_mode_button"),
                                        ("Прескан", "prescan", "https://translator3000.vladya.net/gui.html?utm_source=translator3000_app#work-modes", "prescan_mode_button"),
                                        ("Только БД", "db_only", "https://translator3000.vladya.net/gui.html?utm_source=translator3000_app#work-modes", "db_only_mode_button"),
                                        ("Рилтайм + БД", "realtime", "https://translator3000.vladya.net/gui.html?utm_source=translator3000_app#work-modes", "realtime_mode_button")
                                    ):
                                hbox:
                                    $ x_max_coef = {
                                                "russian": .2,
                                                "english": .2,
                                                "turkish": .12,
                                                "chuvash": .12,
                                                "vietnamese": .17
                                            }.get(translator3000._gui.gui_language, .17)
                                    textbutton translator3000._gui.translate(_name):
                                        style "translator3000_radio_button"
                                        text_style style.translator3000_button_text["top_panel_button"]
                                        background None
                                        xmaximum int((float(store.config.screen_width) * x_max_coef))
                                        yalign .5
                                        action store.SetField(translator3000._gui, "mode", _mode)
                                        hovered translator3000._gui._tooltip_handler.Action(tooltip_id)
                                    if doc_url:
                                        imagebutton:
                                            yalign .5
                                            idle _translator3000_gui.theme.questionMark
                                            hover _translator3000_gui.theme.questionMarkHover
                                            action OpenURL(doc_url)
                                            hovered translator3000._gui._tooltip_handler.Action("docs_button")
                        viewport id "tr3000_main_right_side":
                            yinitial .0
                            mousewheel True
                            pagekeys True
                            has vbox
                            $ _tb_text = "Translator3000. {0}".format(
                                            translator3000._gui.translate("Версия {0}.{1}.{2} ({3}).")
                                        ).format(*(_translator3000.VERSION.version + (_translator3000.VERSION.name.strip(':'), )))
                            if _translator3000.VERSION.is_beta:
                                $ _tb_text += " Beta."
                            textbutton _tb_text:
                                style "translator3000_right_panel_button"
                                text_style style.translator3000_label_text["main_title"]
                                background None
                                action OpenURL("https://boosty.to/nyashniyvladya")
                            for _version_info in (_translator3000.LAST_VERSION, _translator3000.LAST_BETA):
                                if _version_info and (_version_info.version > _translator3000.VERSION.version):
                                    null height _translator3000_gui.resize_from_1080(10, 1)
                                    vbox:
                                        hbox:
                                            label translator3000._gui.translate("Доступно обновление.")
                                            if _version_info.is_beta:
                                                label "{#notTranslate}Beta."
                                        if _version_info.boostyLink:
                                            $ _tb_text = translator3000._gui.translate("Скачать Translator3000 Версия {0}.{1}.{2} ({3}) с Boosty.")
                                            if _version_info.is_beta:
                                                $ _tb_text += " Beta."
                                            textbutton _tb_text.format(*(_version_info.version + (_version_info.name, ))):
                                                style "translator3000_right_panel_button"
                                                text_style "translator3000_button_text"
                                                action OpenURL(_version_info.boostyLink)
                                        if _version_info.patreonLink:
                                            $ _tb_text = translator3000._gui.translate("Скачать Translator3000 Версия {0}.{1}.{2} ({3}) с Patreon.")
                                            if _version_info.is_beta:
                                                $ _tb_text += " Beta."
                                            textbutton _tb_text.format(*(_version_info.version + (_version_info.name, ))):
                                                style "translator3000_right_panel_button"
                                                text_style "translator3000_button_text"
                                                action OpenURL(_version_info.patreonLink)
                                    null height _translator3000_gui.resize_from_1080(10, 1)
                            use translator3000_prescan_status
                            null height _translator3000_gui.resize_from_1080(10, 1)
                            vbox:
                                first_spacing None
                                spacing 1
                                textbutton translator3000._gui.translate("Сервер Discord."):
                                    style "translator3000_right_panel_button"
                                    text_style "translator3000_button_text"
                                    text_size _translator3000_gui.resize_from_1080(30, 1)
                                    action OpenURL("https://discord.gg/FqsQXNH6Fg")
                                textbutton translator3000._gui.translate("Группа в Telegram."):
                                    style "translator3000_right_panel_button"
                                    text_style "translator3000_button_text"
                                    text_size _translator3000_gui.resize_from_1080(30, 1)
                                    action OpenURL("https://t.me/translator3000")
                                textbutton translator3000._gui.translate("Группа ВКонтакте."):
                                    style "translator3000_right_panel_button"
                                    text_style "translator3000_button_text"
                                    text_size _translator3000_gui.resize_from_1080(30, 1)
                                    action OpenURL("https://vk.ru/translator3000")
        elif translator3000._setting["useMinimizeButton"]:
            imagebutton:
                background _translator3000_gui.theme.buttonBack
                hover_background _translator3000_gui.theme.buttonBackHover
                idle _translator3000_gui.theme.maximizeButtonElement
                hover _translator3000_gui.theme.maximizeButtonElementHover
                action ToggleField(translator3000._gui, "show")
                hovered translator3000._gui._tooltip_handler.Action("maximize_button")
                at translator3000_general_window(1., _translator3000_gui.PHI_CONST2)
        if not renpy.get_screen("translator3000_tooltip_screen"):
            use translator3000_tooltip_screen
    screen translator3000_tooltip_screen:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.TOOLTIP_LAYER_NAME
        showif translator3000._gui._tooltip_handler.tt.value:
            window:
                text translator3000._gui._tooltip_handler.tt_text
                at translator3000_tooltip_transform
    screen translator3000_gui_main:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        default edit_window_input_flag = False
        $ _keycommands = translator3000._gui._get_keys()
        if _keycommands["guiShow"]:
            key _keycommands["guiShow"].command action ToggleField(translator3000._gui, "show")
        if _keycommands["databaseTranslateSwitcher"]:
            key _keycommands["databaseTranslateSwitcher"].command action ToggleField(translator3000._gui, "mode", true_value="db_only", false_value="off")
        if _keycommands["displayAlternateTranslations"]:
            key _keycommands["displayAlternateTranslations"].command action (
                ToggleDict(translator3000._setting, "displayAlternateTranslations"),
                translator3000._gui.ApplySettingAction()
            )
        if _keycommands["displayOriginal"]:
            key _keycommands["displayOriginal"].command action (
                CycleDict(translator3000._setting, "displayOriginal", (False, True, "choice_menu_only")),
                translator3000._gui.ApplySettingAction()
            )
        if _keycommands["editWindow"]:
            key _keycommands["editWindow"].command action (
                ToggleDict(translator3000._setting, "showEditWindow"),
                translator3000._gui.ApplySettingAction()
            )
        if _keycommands["forceRestart"]:
            key _keycommands["forceRestart"].command action _translator3000.Translator3000.NeedRestartAction()
        if _keycommands["showMenuInfo"]:
            key _keycommands["showMenuInfo"].command action (
                ToggleDict(translator3000._setting, "showMenuInfo"),
                translator3000._gui.ApplySettingAction(recalculate_choice_menu=True, restart=True)
            )
        use translator3000_base_vbox_in_window(window_sub_style="left_side", cols=2, spacing=5):
            for _pic, txt, act in (
                (_translator3000_gui.theme.supportDeveloper3, "Поддержать разработчика на Boosty", OpenURL("https://boosty.to/nyashniyvladya")),
                (_translator3000_gui.theme.supportDeveloper4, "Поддержать разработчика на Patreon", OpenURL("https://www.patreon.com/join/NyashniyVladya")),
                (_translator3000_gui.theme.variablesEditor, "Редактировать переменные игры", (Function(translator3000.vars_changer._screen_init), translator3000._gui.ForwardAction("translator3000_change_variables"))),
                (_translator3000_gui.theme.translatorSetting, "Настройки переводчика", translator3000._gui.ForwardAction("translator3000_user_preferences")),
                (
                    _translator3000_gui.theme.menuExpand,
                    "Расширение меню выборов",
                    (
                        ToggleDict(translator3000._setting, "showMenuInfo"),
                        translator3000._gui.ApplySettingAction(recalculate_choice_menu=True, restart=True)
                    )
                ),
                (_translator3000_gui.theme.clearLocalCache, "Очистить кэш переводов игры", translator3000._gui.ConfirmAction("Кэш переводов для игры будет очищен.", Function(translator3000.clear_local_cache))),
                (_translator3000_gui.theme.clearAllCache, "Очистить весь кэш переводов", translator3000._gui.ConfirmAction("Кэш переводов будет очищен.", Function(translator3000.clear_cache))),
                (_translator3000_gui.theme.statButton2, "Статистика", translator3000._gui.ForwardAction("translator3000_stat")),
                (_translator3000_gui.theme.backupDB, "Сделать бэкап БД", Function(translator3000.backup_database)),
                (
                    _translator3000_gui.theme.textEditorWindow,
                    "Вывести окно редактирования текста", (
                        ToggleDict(translator3000._setting, "showEditWindow"),
                        translator3000._gui.ApplySettingAction()
                    )
                ),
            ):
                button:
                    style "translator3000_main_menu_button"
                    action act
                    has vbox
                    xysize (_translator3000_gui.resize_from_1080(300, 2), _translator3000_gui.resize_from_1080(300, 2))
                    xalign .5
                    showif txt == "Статистика":
                        $ perc = "{0: >3.0%}".format(translator3000._gui.game_passing_percentage())[:-1]
                        showif perc == "100":
                            add _translator3000_gui.theme.statButton2ReadAll:
                                align (.5, .5)
                        else:
                            fixed:
                                align (.5, .5)
                                xysize (_translator3000_gui.resize_from_1080(90, 2), _translator3000_gui.resize_from_1080(90, 2))
                                add _translator3000_gui.theme.statButton2:
                                    align (.5, .5)
                                text "{{#notTranslate}}{0}".format(perc):
                                    anchor (.5, .5)
                                    pos (.535, .27)
                                    kerning 17.
                                    size _translator3000_gui.resize_from_1080(35, 1)
                    else:
                        add _pic:
                            align (.5, .5)
                    text translator3000._gui.translate(txt):
                        xalign .5
                        text_align .5
        $ _mode_extra_window = (translator3000._setting["workMethod"] == "translateInExtraWindow")
        if (_mode_extra_window and translator3000._translator_switcher) or translator3000._setting["displayOriginal"]:
            $ _txts = None
            if (_mode_extra_window or (translator3000._setting["displayOriginal"] is True)) and hasattr(renpy.store, "_last_raw_what") and renpy.store._last_raw_what:
                $ _txts = (renpy.store._last_raw_what, )
            elif "menu" in _translator3000._CURRENT_STATAMENT:
                $ menu_data = translator3000._gui._choice_menu_object.get_current_menu(True)
                if menu_data:
                    $ _txts = menu_data
            if _txts:
                $ _txts = tuple(
                    _translator3000.builtins.map(
                        (translator3000 if _mode_extra_window else (lambda x: (translator3000._original_mapping[x][0] if (x in translator3000._original_mapping) else x))),
                        _txts
                    )
                )
                use translator3000_draggable_window(translator3000._gui._orig_text_screen_data, True):
                    vbox:
                        for _i, _txt in enumerate(_txts, 1):
                            hbox:
                                xalign translator3000._gui._orig_text_screen_data._text_align
                                for _t in ((_i, _txt) if (len(_txts) > 1) else (_txt, )):
                                    window:
                                        text "{{#notTranslate}}{0}".format(_t):
                                            text_align translator3000._gui._orig_text_screen_data._text_align
                                            size translator3000._gui._orig_text_screen_data.size
        if translator3000._setting["showEditWindow"]:
            $ _enter_action = (
                SetField(translator3000._multi_persistent, "use_edit", True),
                Function(translator3000._multi_persistent.save),
                Function(translator3000.backup_database),
                SetScreenVariable("edit_window_input_flag", False),
                _translator3000.Translator3000.NeedRestartAction()
            )
            $ _value = _translator3000_gui._LastSayEditValue._create_value_object(_enter_action, translator3000)
            use translator3000_draggable_window(translator3000._gui._edit_text_screen_data, True):
                if _value:
                    if edit_window_input_flag:
                        vbox:
                            xalign translator3000._gui._edit_text_screen_data._text_align
                            input:
                                style "translator3000_input_text"
                                if translator3000._setting["extraTextOptions"]["font"] is not None:
                                    font translator3000._fonts._get_font(
                                        translator3000._setting["extraTextOptions"]["font"]
                                    )
                                size translator3000._gui._edit_text_screen_data.size
                                value _value
                            textbutton translator3000._gui.translate("Сохранить."):
                                text_size translator3000._gui._edit_text_screen_data.size
                                action _enter_action
                    else:
                        vbox:
                            xalign translator3000._gui._edit_text_screen_data._text_align
                            $ _txt = _value.get_text()
                            if not _txt.strip():
                                $ _txt = "..."
                            textbutton "{{#notTranslate}}{0}".format(translator3000.quote(_txt)):
                                style "translator3000_input_text"
                                if translator3000._setting["extraTextOptions"]["font"] is not None:
                                    text_font translator3000._fonts._get_font(
                                        translator3000._setting["extraTextOptions"]["font"]
                                    )
                                focus_mask None
                                xalign translator3000._gui._edit_text_screen_data._text_align
                                text_size translator3000._gui._edit_text_screen_data.size
                                action SetScreenVariable("edit_window_input_flag", True)
                        if not _value.is_translated_mark:
                            text translator3000._gui.translate("Перевод не найден."):
                                xalign translator3000._gui._edit_text_screen_data._text_align
                                text_align translator3000._gui._edit_text_screen_data._text_align
                                size translator3000._gui._edit_text_screen_data.size
                else:
                    text translator3000._gui.translate("Редактирование невозможно."):
                        xalign translator3000._gui._edit_text_screen_data._text_align
                        text_align translator3000._gui._edit_text_screen_data._text_align
                        size translator3000._gui._edit_text_screen_data.size
        if translator3000._setting["displayAlternateTranslations"]:
            if hasattr(renpy.store, "_last_raw_what") and renpy.store._last_raw_what and (renpy.store._last_raw_what in translator3000._original_mapping):
                $ _other_translates = translator3000.get_all_available_translates(translator3000._original_mapping[renpy.store._last_raw_what][0], include_current_service=False)
                if _other_translates:
                    use translator3000_draggable_window(translator3000._gui._alternate_text_screen_data, True):
                        vbox:
                            xalign translator3000._gui._alternate_text_screen_data._text_align
                            for srv, txt in _other_translates.items():
                                window:
                                    has vbox
                                    label "{{#notTranslate}}{0}".format(translator3000.quote(srv)):
                                        xalign translator3000._gui._alternate_text_screen_data._text_align
                                        text_size (translator3000._gui._alternate_text_screen_data.size + 3)
                                    window:
                                        text "{{#notTranslate}}{{size={1}}}{0}{{/size}}".format(txt, translator3000._gui._alternate_text_screen_data.size):
                                            xalign translator3000._gui._alternate_text_screen_data._text_align
                                            text_align translator3000._gui._alternate_text_screen_data._text_align
                                            size translator3000._gui._alternate_text_screen_data.size
        if translator3000._setting["showMenuInfo"]:
            $ menu_data = translator3000._gui._choice_menu_object.get_current_menu()
            if menu_data:
                $ last_pycode = None
            else:
                $ last_pycode = translator3000._gui._choice_menu_object.get_last_py_code()
            if menu_data or last_pycode:
                use translator3000_draggable_window(translator3000._gui._menu_info_data, True):
                    window:
                        if menu_data:
                            vbox:
                                for _i, (_label, _condition, condition, py_code) in enumerate(menu_data, 1):
                                    window:
                                        has vbox
                                        hbox:
                                            window:
                                                text "{{#notTranslate}}{0}".format(_i):
                                                    text_align translator3000._gui._menu_info_data._text_align
                                                    size translator3000._gui._menu_info_data.size
                                                    bold True
                                            window:
                                                label "{{#notTranslate}}{{size={1}}}{0}{{/size}}".format(translator3000(_label), translator3000._gui._menu_info_data.size):
                                                    text_size translator3000._gui._menu_info_data.size
                                            if not condition:
                                                window:
                                                    text translator3000._gui.translate("Скрытый вариант"):
                                                        text_align translator3000._gui._menu_info_data._text_align
                                                        size translator3000._gui._menu_info_data.size
                                        if _condition != "True":
                                            hbox:
                                                window:
                                                    text translator3000._gui.translate("Условие показа:"):
                                                        text_align translator3000._gui._menu_info_data._text_align
                                                        size translator3000._gui._menu_info_data.size
                                                window:
                                                    text "{{#notTranslate}}({0})".format(_condition):
                                                        text_align translator3000._gui._menu_info_data._text_align
                                                        size translator3000._gui._menu_info_data.size
                                        if py_code:
                                            window:
                                                has vbox
                                                for py_string in map(translator3000.quote, py_code):
                                                    text "{{#notTranslate}}{0}".format(py_string):
                                                        text_align translator3000._gui._menu_info_data._text_align
                                                        size translator3000._gui._menu_info_data.size
                        elif last_pycode:
                            window:
                                has vbox
                                label translator3000._gui.translate("Последний выполненный код:"):
                                    text_size (translator3000._gui._menu_info_data.size + 2)
                                window:
                                    has vbox
                                    for py_string in map(translator3000.quote, last_pycode):
                                        text "{{#notTranslate}}{0}".format(py_string):
                                            text_align translator3000._gui._menu_info_data._text_align
                                            size translator3000._gui._menu_info_data.size
        if translator3000._gui._message_handler.show:
            use translator3000_draggable_window(translator3000._gui._messages_screen_data, False, xmaximum=int((float(store.config.screen_width) * _translator3000_gui.PHI_CONST2)), ymaximum=int((float(store.config.screen_height) * _translator3000_gui.PHI_CONST2)), xpadding=_translator3000_gui.resize_from_1080(30, 0), ypadding=_translator3000_gui.resize_from_1080(50, 0)):
                vbox:
                    spacing _translator3000_gui.resize_from_1080(40, 0)
                    imagebutton:
                        xalign .99
                        background _translator3000_gui.theme.buttonBack
                        hover_background _translator3000_gui.theme.buttonBackHover
                        idle _translator3000_gui.theme.closeButtonElement
                        hover _translator3000_gui.theme.closeButtonElementHover
                        action (
                            SetField(translator3000._gui._message_handler, "show", False),
                            translator3000._gui._tooltip_handler.DismissAction()
                        )
                        hovered translator3000._gui._tooltip_handler.Action("close_window_button")
                    textbutton translator3000._gui.translate("Прочитать все"):
                        xalign translator3000._gui._messages_screen_data._text_align
                        action (
                            SelectedIf((not translator3000._gui._message_handler.is_have_unread())),
                            Function(translator3000._gui._message_handler.mark_all_as_read)
                        )
                    hbox:
                        first_spacing None
                        spacing _translator3000_gui.resize_from_1080(30, 1)
                        window:
                            has viewport id "tr3000_messages_vp"
                            yinitial .0
                            mousewheel True
                            pagekeys True
                            vbox:
                                for message_id, message, is_readed in translator3000._gui._message_handler.get_messages():
                                    window:
                                        xalign translator3000._gui._messages_screen_data._text_align
                                        has vbox
                                        spacing _translator3000_gui.resize_from_1080(20, 0)
                                        text "{{#notTranslate}}{0}".format(message):
                                            text_align translator3000._gui._messages_screen_data._text_align
                                            xalign translator3000._gui._messages_screen_data._text_align
                                        textbutton translator3000._gui.translate("Прочитано"):
                                            style "translator3000_check_button"
                                            text_style "translator3000_button_text"
                                            xalign translator3000._gui._messages_screen_data._text_align
                                            action (
                                                        SelectedIf(is_readed),
                                                        Function(translator3000._gui._message_handler.mark_as_read, message_id)
                                                    )
                        vbox:
                            first_spacing None
                            spacing _translator3000_gui.resize_from_1080(5, 1)
                            yalign .5
                            imagebutton:
                                xalign .5
                                background _translator3000_gui.theme.buttonBack
                                hover_background _translator3000_gui.theme.buttonBackHover
                                idle _translator3000_gui.theme.arrowUp
                                hover _translator3000_gui.theme.arrowUpHover
                                action Scroll("tr3000_messages_vp", "vertical decrease")
                                hovered translator3000._gui._tooltip_handler.Action("arrow_up_button")
                            vbar:
                                style "translator3000_vbar"
                                xalign .5
                                value YScrollValue("tr3000_messages_vp")
                                hovered translator3000._gui._tooltip_handler.Action("vbar_element")
                            imagebutton:
                                xalign .5
                                background _translator3000_gui.theme.buttonBack
                                hover_background _translator3000_gui.theme.buttonBackHover
                                idle _translator3000_gui.theme.arrowDown
                                hover _translator3000_gui.theme.arrowDownHover
                                action Scroll("tr3000_messages_vp", "vertical increase")
                                hovered translator3000._gui._tooltip_handler.Action("arrow_down_button")
    screen translator3000_draggable_window(drag_object, add_text_size_block=False, **window_props):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        drag:
            draggable True
            focus_mask None
            dragged drag_object._dragged
            xpos drag_object.x
            ypos drag_object.y
            has window
            at translator3000_extra_windows(persistent.tr3000_alpha_main_window, persistent.tr3000_zoom_main_window)
            if window_props:
                properties window_props
            if add_text_size_block:
                hbox:
                    if drag_object._text_align > .5:
                        box_reverse True
                    window:
                        xalign drag_object._text_align
                        has vbox
                        xalign drag_object._text_align
                        textbutton "{#notTranslate}+":
                            text_size _translator3000_gui.resize_from_1080(15, 0)
                            action SetField(drag_object, "size", (drag_object.size + 1))
                            hovered translator3000._gui._tooltip_handler.Action("text_size_plus_button")
                        if drag_object.size >= 5:
                            textbutton "{#notTranslate}-":
                                text_size _translator3000_gui.resize_from_1080(15, 0)
                                action SetField(drag_object, "size", (drag_object.size - 1))
                                hovered translator3000._gui._tooltip_handler.Action("text_size_minus_button")
                    transclude
            else:
                transclude
    screen translator3000_confirm_screen(message, yes_action):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window:
            label translator3000._gui.translate(message)
            textbutton translator3000._gui.translate("Да."):
                action (yes_action, translator3000._gui.BackAction())
                hovered translator3000._gui._tooltip_handler.Action("yes_button")
            textbutton translator3000._gui.translate("Нет."):
                action translator3000._gui.BackAction()
                hovered translator3000._gui._tooltip_handler.Action("no_button")
    screen translator3000_gui_language:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window:
            label translator3000._gui.translate("Язык интерфейса (не перевода).")
            for t in sorted(translator3000._gui.available_languages):
                textbutton "{{#notTranslate}}{0}".format(translator3000.quote(t).title()):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    action SetField(translator3000._gui, "gui_language", t)
    screen translator3000_set_language(field_name, dest_direction):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window(use_mini_window=False):
            vbox:
                label translator3000._gui.translate("Выбор языка.")
                use translator3000_mini_window(cols=2, spacing=_translator3000_gui.resize_from_1080(8, 1)):
                    for code in translator3000.get_all_lang_codes(dest_direction=dest_direction):
                        textbutton "{{#notTranslate}}{0}".format(
                            translator3000.quote(
                                translator3000._translator_object.get_lang_name(translator3000._translationService, code, dest_direction=dest_direction)
                            ).title()
                        ):
                            style "translator3000_radio_button"
                            text_style "translator3000_button_text"
                            xsize _translator3000_gui.resize_from_1080(300, 2)
                            ysize _translator3000_gui.resize_from_1080(90, 1)
                            align (.0, .5)
                            action (
                                SetDict(translator3000._setting, field_name, code),
                                translator3000._gui.ApplySettingAction(True, language_check=True)
                            )
    screen translator3000_choice_key_command(param_name):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        default analyzer = _translator3000_gui.PressKeyAnalyzer(
            pressed_data=translator3000._setting["keys"][param_name],
            default_value=translator3000.DEFAULT_SETTING["keys"][param_name]
        )
        default current_pressed = analyzer.pressed
        add analyzer
        use translator3000_base_vbox_in_window:
            label translator3000._gui.translate("Выбор комбинации клавиш.")
            text translator3000._gui.translate("Выберите желаемую комбинацию клавиш на клавиатуре.")
            if analyzer.pressed:
                $ _mods = analyzer.pressed.mods
                vbox:
                    if _mods:
                        window:
                            has vbox
                            label translator3000._gui.translate("Модификаторы.")
                            hbox:
                                for mod_name in _mods:
                                    text "{{#notTranslate}}{0}".format(mod_name)
                    window:
                        has vbox
                        label translator3000._gui.translate("Основная клавиша.")
                        text "{{#notTranslate}}{0}".format(analyzer.pressed.name)
                    if current_pressed != analyzer.pressed:
                        textbutton translator3000._gui.translate("Установить указанную комбинацию."):
                            action (
                                SetDict(translator3000._setting["keys"], param_name, analyzer.pressed.as_setting_param),
                                SetScreenVariable("current_pressed", analyzer.pressed),
                                translator3000._gui.ApplySettingAction()
                            )
            else:
                label translator3000._gui.translate("Ожидание нажатия.")
            if current_pressed != analyzer.default_pressed:
                textbutton translator3000._gui.translate("По умолчанию."):
                    if analyzer.default_pressed:
                        action (
                            SetDict(translator3000._setting["keys"], param_name, analyzer.default_pressed.as_setting_param),
                            SetScreenVariable("current_pressed", analyzer.default_pressed),
                            SetField(analyzer, "pressed", analyzer.default_pressed),
                            translator3000._gui.ApplySettingAction()
                        )
                    else:
                        action (
                            SetDict(translator3000._setting["keys"], param_name, None),
                            SetScreenVariable("current_pressed", None),
                            SetField(analyzer, "pressed", None),
                            translator3000._gui.ApplySettingAction()
                        )
            if current_pressed:
                textbutton translator3000._gui.translate("Отключить комбинацию."):
                    action (
                        SetDict(translator3000._setting["keys"], param_name, None),
                        SetScreenVariable("current_pressed", None),
                        SetField(analyzer, "pressed", None),
                        translator3000._gui.ApplySettingAction()
                    )
    screen translator3000_sample_text:
        tag translator3000_screen
        style_prefix "say"
        layer _translator3000.SCREEN_LAYER_NAME
        input:
            style "translator3000_input_text"
            align (.5, .5)
            value FieldInputValue(translator3000._gui, "_sample_text")
        window:
            yalign 1.
            text "{{#notTranslate}}{0}".format(
                translator3000.quote(translator3000._gui._sample_text)
            ):
                layout "tex"
                align (
                    _translator3000_gui.PHI_CONST2,
                    _translator3000_gui.PHI_CONST
                )
                properties translator3000._get_text_props()
    screen translator3000_set_font(from_game=True):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        default current_dir = ("" if from_game else translator3000._gui._fs_object.desktop)
        use translator3000_sample_text
        use translator3000_base_vbox_in_window:
            label translator3000._gui.translate("Настройки шрифта.")
            if translator3000._setting["extraTextOptions"]["font"] is not None:
                text "{{#notTranslate}}{0}".format(
                    translator3000.quote(translator3000._gui._fs_object.get_clear_filename(translator3000._setting["extraTextOptions"]["font"]))
                ):
                    size _translator3000_gui.resize_from_1080(30, 1)
            if from_game == "from_database":
                for fnt in sorted(tuple(translator3000._fonts.get_available_fonts())):
                    textbutton "{{#notTranslate}}{0}".format(translator3000.quote(translator3000._gui._fs_object.get_clear_filename(fnt))):
                        action Function(
                            translator3000._gui._set_font_pref,
                            fnt,
                            from_renpy="from_database"
                        )
            elif from_game == "from_system_fonts":
                for name, fnt in sorted(tuple(translator3000._fonts.get_system_fonts())):
                    textbutton "{{#notTranslate}}{0}".format(translator3000.quote(name)):
                        action Function(
                            translator3000._gui._set_font_pref,
                            fnt,
                            from_renpy=False,
                            save_name=name
                        )
            else:
                if current_dir:
                    text "{{#notTranslate}}{0}".format(current_dir)
                    textbutton translator3000._gui.translate("Перейти в предыдущую директорию."):
                        action SetScreenVariable(
                            "current_dir",
                            translator3000._gui._fs_object.dirname(current_dir, from_game)
                        )
                null height _translator3000_gui.resize_from_1080(30, 1)
                vbox:
                    $ data_in_dir = translator3000._gui._fs_object.listdir(current_dir, from_game)
                    for _directory in data_in_dir["dirs"]:
                        $ full_path = translator3000._gui._fs_object.join(
                            current_dir,
                            _directory,
                            from_renpy=from_game
                        )
                        textbutton translator3000._gui.translate("Перейти в \"{0}\".").format(
                            translator3000.quote(_directory)
                        ):
                            action SetScreenVariable("current_dir", full_path)
                    null height _translator3000_gui.resize_from_1080(10, 1)
                    for _filename in data_in_dir["files"]:
                        $ full_path = translator3000._gui._fs_object.join(
                            current_dir,
                            _filename,
                            from_renpy=from_game
                        )
                        $ ext = _translator3000_gui.path.splitext(full_path)[1]
                        if ext.lower() in _translator3000.font_storage.available_font_exts:
                            textbutton "{{#notTranslate}}{0}".format(
                                translator3000.quote(
                                    translator3000._gui._fs_object.get_clear_filename(_filename)
                                )
                            ):
                                action Function(
                                    translator3000._gui._set_font_pref,
                                    full_path,
                                    from_renpy=from_game
                                )
    screen translator3000_color_choice(changed_dict, _key):
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        default _picker = translator3000._gui._color_picker(changed_dict, _key)
        vbox:
            transclude
            hbox:
                vbar value FieldValue(
                    _picker,
                    "brightness",
                    offset=(-1.),
                    range=2.,
                    step=.01
                ):
                    ysize _picker.color_circle_size[1]
                    yalign 1.
                add _picker:
                    yalign 1.
    screen translator3000_extra_text_preferences:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_sample_text
        use translator3000_base_vbox_in_window:
            window:
                has vbox
                textbutton translator3000._gui.translate("Курсивный текст."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                            ToggleDict(translator3000._setting["extraTextOptions"], "italic"),
                            translator3000._gui.ApplySettingAction()
                        )
                textbutton translator3000._gui.translate("Жирный текст."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                            ToggleDict(translator3000._setting["extraTextOptions"], "bold"),
                            translator3000._gui.ApplySettingAction()
                        )
            window:
                use translator3000_color_choice(translator3000._setting["extraTextOptions"], "color"):
                    label translator3000._gui.translate("Цвет.")
                    if translator3000._setting["extraTextOptions"]["color"] is not None:
                        $ _color = renpy.color.Color(translator3000._setting["extraTextOptions"]["color"])
                        text "{{#notTranslate}}{0}".format(_color.hexcode)
            window:
                has vbox
                label translator3000._gui.translate("Размер.")
                if translator3000._setting["extraTextOptions"]["size"] is None:
                    text translator3000._gui.translate("Не установлено.")
                else:
                    text "{{#notTranslate}}{size}".format(**translator3000._setting["extraTextOptions"]):
                        size _translator3000_gui.resize_from_1080(30, 1)
                bar value FieldValue(
                        translator3000._gui,
                        "_text_size_pref",
                        range=300,
                        step=1
                    )
            window:
                has vbox
                label translator3000._gui.translate("Обводка.")
                if translator3000._setting["extraTextOptions"]["outlines"]:
                    vbox:
                        for n, _outlines in reversed(tuple(enumerate(translator3000._setting["extraTextOptions"]["outlines"][:]))):
                            $ _size, _color, _xo, _yo = _outlines
                            window:
                                has vbox
                                label translator3000._gui.translate("Слой {0}.").format((n + 1))
                                window:
                                    has vbox
                                    label translator3000._gui.translate("Размер слоя {0}.").format((n + 1))
                                    bar value DictValue(
                                        translator3000._setting["extraTextOptions"]["outlines"][n],
                                        0,
                                        range=25,
                                        step=1,
                                        action=translator3000._gui.ApplySettingAction()
                                    )
                                window:
                                    use translator3000_color_choice(translator3000._setting["extraTextOptions"]["outlines"][n], 1):
                                        label translator3000._gui.translate("Цвет слоя {0}.").format((n + 1))
                                        text "{{#notTranslate}}{0}".format(renpy.color.Color(_color).hexcode)
                                window:
                                    has vbox
                                    for axis, _i in (('X', 2), ('Y', 3)):
                                        window:
                                            has vbox
                                            label translator3000._gui.translate("Смещение слоя {0} по оси {1}.").format((n + 1), axis)
                                            bar value DictValue(
                                                translator3000._setting["extraTextOptions"]["outlines"][n],
                                                _i,
                                                range=300,
                                                step=1,
                                                action=translator3000._gui.ApplySettingAction()
                                            )
                                textbutton translator3000._gui.translate("Удалить слой {0}.").format((n + 1)):
                                    action (
                                        RemoveFromSet(translator3000._setting["extraTextOptions"]["outlines"], _outlines),
                                        translator3000._gui.ApplySettingAction()
                                    )
                else:
                    text translator3000._gui.translate("Не установлено.")
                textbutton translator3000._gui.translate("Добавить слой."):
                    action (
                        If(
                            (translator3000._setting["extraTextOptions"]["outlines"] is None),
                            SetDict(translator3000._setting["extraTextOptions"], "outlines", _translator3000.builtins.list((_translator3000.builtins.list((1, "#000", 0, 0)), ))),
                            Function((lambda a: translator3000._setting["extraTextOptions"]["outlines"].insert(0, a)), _translator3000.builtins.list((1, "#000", 0, 0)))
                        ),
                        translator3000._gui.ApplySettingAction()
                    )
            window:
                has vbox
                label translator3000._gui.translate("Шрифт.")
                if translator3000._setting["extraTextOptions"]["font"] is None:
                    text translator3000._gui.translate("Не установлено.")
                else:
                    if translator3000._setting["extraTextOptions"]["font"] == _translator3000.AUTO_PARAM_STRING:
                        text translator3000._gui.translate("Автозагрузка."):
                            size _translator3000_gui.resize_from_1080(30, 1)
                    else:
                        text "{{#notTranslate}}{0}".format(
                                translator3000.quote(translator3000._gui._fs_object.get_clear_filename(translator3000._setting["extraTextOptions"]["font"]))
                            ):
                            size _translator3000_gui.resize_from_1080(30, 1)
                    textbutton translator3000._gui.translate("Сбросить."):
                        action (
                                SetDict(translator3000._setting["extraTextOptions"], "font", None),
                                translator3000._gui.ApplySettingAction()
                            )
                textbutton translator3000._gui.translate("Выбрать из файлов игры."):
                    action translator3000._gui.ForwardAction(
                            "translator3000_set_font",
                            from_game=True
                        )
                textbutton translator3000._gui.translate("Выбрать из файлов ПК."):
                    action translator3000._gui.ForwardAction(
                            "translator3000_set_font",
                            from_game=False
                        )
                textbutton translator3000._gui.translate("Выбрать из системных шрифтов."):
                    action translator3000._gui.ForwardAction(
                            "translator3000_set_font",
                            from_game="from_system_fonts"
                        )
                textbutton translator3000._gui.translate("Выбрать из использовавшихся ранее."):
                    action translator3000._gui.ForwardAction(
                            "translator3000_set_font",
                            from_game="from_database"
                        )
                textbutton translator3000._gui.translate("Автозагрузка."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                            SetDict(translator3000._setting["extraTextOptions"], "font", _translator3000.AUTO_PARAM_STRING),
                            translator3000._gui.ApplySettingAction()
                        )
                    hovered translator3000._gui._tooltip_handler.Action("auto_load_font_button")
    screen translator3000_user_preferences:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window(translator3000._gui.ApplySettingAction(), first_spacing=None, spacing=_translator3000_gui.resize_from_1080(20), background=None):
            textbutton translator3000._gui.translate("Настроить параметры отображаемого текста."):
                action translator3000._gui.ForwardAction(
                    "translator3000_extra_text_preferences"
                )
            textbutton translator3000._gui.translate("Сбросить настройки уведомлений всплывающих окон."):
                action Function(translator3000.popup_windows_handler._reset_stats)
            window:
                has vbox
                for _label, _key, _dest_direction in (
                    ("Исходный язык игры.", "gameLanguage", False),
                    ("Направление перевода.", "directionOfTranslation", True)
                ):
                    window:
                        has vbox
                        label translator3000._gui.translate(_label)
                        if translator3000._setting[_key] is None:
                            text translator3000._gui.translate("Не установлено.")
                        else:
                            text "{{#notTranslate}}{0}".format(
                                translator3000.quote(
                                    translator3000._translator_object.get_lang_name(
                                        translator3000._translationService,
                                        translator3000._setting[_key],
                                        dest_direction=_dest_direction
                                    )
                                ).title()
                            )
                        textbutton translator3000._gui.translate("Сменить."):
                            action translator3000._gui.ForwardAction(
                                "translator3000_set_language",
                                field_name=_key,
                                dest_direction=_dest_direction
                            )
            window:
                has vbox
                label translator3000._gui.translate("Булевые параметры.")
                textbutton translator3000._gui.translate("Режим отладки."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "_debug_mode"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Сохранять оригинал в истории."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "originalInHistory"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Подставлять переменные из загруженной базы данных."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "addVariablesFromDB"),
                        translator3000._gui.ApplySettingAction(True)
                    )
                textbutton translator3000._gui.translate("Использовать видимую кнопку отображения переводчика."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "useMinimizeButton"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Использовать альтернативный метод сортировки в предварительном сканировании"):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "alternativeSortMethod"),
                        translator3000._gui.ApplySettingAction(True)
                    )
                textbutton translator3000._gui.translate("Показывать альтернативные переводы"):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "displayAlternateTranslations"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Использовать режим \"без задержки\""):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "useNoFreezeLogic"),
                        translator3000._gui.ApplySettingAction()
                    )
            window:
                has vbox
                label translator3000._gui.translate("Показывать оригинал на экране.")
                textbutton translator3000._gui.translate("Отключено."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", False),
                            translator3000._gui.ApplySettingAction()
                        )
                textbutton translator3000._gui.translate("Весь текст."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", True),
                            translator3000._gui.ApplySettingAction()
                        )
                textbutton translator3000._gui.translate("Только текст в меню выборов."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", "choice_menu_only"),
                            translator3000._gui.ApplySettingAction()
                        )
            window:
                has vbox
                label translator3000._gui.translate("Сервис перевода.")
                $ services = translator3000._translator_object.get_available_translator_services()
                for _group, srvs in services:
                    window:
                        has vbox
                        text "{{#notTranslate}}{0}".format(translator3000.quote(_group))
                        for srv in srvs:
                            textbutton "{{#notTranslate}}{0}".format(translator3000.quote(srv)):
                                style "translator3000_radio_button"
                                text_style "translator3000_button_text"
                                action (
                                    SetField(translator3000, "_translationService", srv),
                                    translator3000._gui.ApplySettingAction(True, language_check=True, interrupt_translations=True)
                                )
            window:
                has vbox
                label translator3000._gui.translate("Комбинации клавиш.")
                textbutton translator3000._gui.translate("Показ/скрытие окна переводчика"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "guiShow")
                textbutton translator3000._gui.translate("Включить/выключить перевод в режиме БД"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "databaseTranslateSwitcher")
                textbutton translator3000._gui.translate("Показ/скрытие оригинального текста"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "displayOriginal")
                textbutton translator3000._gui.translate("Показ/скрытие альтернативного перевода"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "displayAlternateTranslations")
                textbutton translator3000._gui.translate("Показ/скрытие окна редактирования текста"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "editWindow")
                textbutton translator3000._gui.translate("Обновить страницу"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "forceRestart")
                textbutton translator3000._gui.translate("Включить/выключить расширение меню выборов"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "showMenuInfo")
            window:
                has vbox
                label translator3000._gui.translate("Способ работы переводчика.")
                textbutton translator3000._gui.translate("Перевод диалогов и меню."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "dialogueOnly"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
                textbutton translator3000._gui.translate("Перевод в отдельном окне."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "translateInExtraWindow"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
                textbutton translator3000._gui.translate("Перевод всего текста в игре (Бета)."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "allText"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
            if not translator3000._translator_object._get_translator(translator3000._translationService).BROWSER_TRANSLATOR:
                window:
                    has vbox
                    label translator3000._gui.translate("Частота запросов.")
                    if (_translator3000.os.getenv("TRANSLATOR3000_DISABLE_RPM_LIMITS", '0') != '1') and (translator3000._translator_object._get_translator(translator3000._translationService).FORCE_RPM is not None):
                        text translator3000._gui.translate("Для этого сервиса перевода частота фиксированная.")
                    else:
                        if translator3000._setting["requestsFrequency"] is None:
                            text translator3000._gui.translate("Не установлено.")
                        else:
                            text translator3000._gui.translate("{0:.0f} запросов в минуту.").format(
                                float(translator3000._setting["requestsFrequency"])
                            )
                        bar value FieldValue(
                            translator3000._gui,
                            "requests_frequency_pref",
                            offset=10.,
                            range=500.,
                            step=.01
                        )
    screen translator3000_prescan_status:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        vbox:
            if translator3000._stat_object.current_game.strings_len and translator3000._stat_object.current_game.symbols_len:
                text translator3000._gui.translate("В игре {0} строк ({1} символов).").format(
                    translator3000._stat_object.current_game.strings_len,
                    translator3000._stat_object.current_game.symbols_len
                )
            null height _translator3000_gui.resize_from_1080(5, 1)
            if translator3000._translate_preparer.state == "reloading":
                text translator3000._gui.translate("Выполняется перезапуск предварительного сканирования."):
                    bold True
                    size _translator3000_gui.resize_from_1080(35, 1)
            elif (translator3000._translate_preparer.state in ("preparing", "scanning", "assembling")) and translator3000._translate_preparer._switcher:
                text translator3000._gui.translate("Подготовка потока предварительного сканирования."):
                    bold True
                    size _translator3000_gui.resize_from_1080(35, 1)
                null height 5
                text translator3000._gui.translate("Процесс подготовки может занять несколько минут, в зависимости от размера.")
                text translator3000._gui.translate("Может показаться, что процесс \"завис\", но это не так. Если игра большая, подготовка может занимать минуты.")
                null height 5
                if translator3000._translate_preparer.state == "assembling":
                    text translator3000._gui.translate("Выполняется сборка строк."):
                        bold True
                        size _translator3000_gui.resize_from_1080(35, 1)
                elif translator3000._translate_preparer.state == "scanning":
                    text translator3000._gui.translate("Подготовлено {done} частей.").format(**translator3000._translate_preparer.get_info()):
                        bold True
                        size _translator3000_gui.resize_from_1080(35, 1)
            elif (translator3000._translate_preparer.state == "check_remote_db") and translator3000._translate_preparer._switcher:
                text translator3000._gui.translate("Проверка доступности готового перевода."):
                    bold True
                    size _translator3000_gui.resize_from_1080(35, 1)
            elif (translator3000._translate_preparer.state in ("first_scan", "working", "finalizing")) and translator3000._translate_preparer._switcher:
                if translator3000._translate_preparer.state in ("first_scan", "working"):
                    $ _txt = ("Перевод строк." if (translator3000._translate_preparer.state == "first_scan") else "Дополнительный перевод.")
                    text translator3000._gui.translate(_txt):
                        bold True
                        size _translator3000_gui.resize_from_1080(35, 1)
                    text translator3000._gui.translate("Выполнено {done} запросов из {total}.").format(**translator3000._translate_preparer.get_info())
                elif translator3000._translate_preparer.state == "finalizing":
                    text translator3000._gui.translate("Завершение процесса. Итоговая проверка базы."):
                        bold True
                        size _translator3000_gui.resize_from_1080(35, 1)
                    text translator3000._gui.translate("Проверено {done} частей из {total}.").format(**translator3000._translate_preparer.get_info())
                text "{{#notTranslate}}{0}".format("{0:.1%}".format(translator3000._translate_preparer.status))
                bar value StaticValue(translator3000._translate_preparer.status)
            elif translator3000._translate_preparer.state == "almost_done":
                text translator3000._gui.translate("Завершение. Почти готово...")
            elif translator3000._translate_preparer.state == "done":
                if translator3000._translate_preparer.has_exception():
                    text translator3000._gui.translate("Возникла ошибка в потоке сканирования."):
                        bold True
                        size _translator3000_gui.resize_from_1080(35, 1)
                    textbutton translator3000._gui.translate("Бросить трейсбек."):
                        style "translator3000_right_panel_button"
                        text_style "translator3000_button_text"
                        action Function(translator3000._translate_preparer._raise_from_thread)
                elif translator3000._translate_preparer.is_completed():
                    text translator3000._gui.translate("Предварительное сканирование закончено.")
            null height _translator3000_gui.resize_from_1080(5, 1)
            text translator3000._gui.translate("Для корректного перевода убедитесь, перед запуском сканирования, что все динамические данные (имя игрока и подобные) введены.")
            text translator3000._gui.translate("В противном случае введите их и перезапустите предварительно сканирование.")
            null height _translator3000_gui.resize_from_1080(5, 1)
            textbutton translator3000._gui.translate("Перезапустить предварительное сканирование."):
                style "translator3000_right_panel_button"
                text_style "translator3000_button_text"
                action Function(translator3000._translate_preparer.restart)
    screen translator3000_stat:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        timer .5 action Function(renpy.restart_interaction) repeat True
        use translator3000_base_vbox_in_window:
            label translator3000._gui.translate("Статистика.")
            for _ind, _game in enumerate(translator3000._stat_object.game_list):
                window:
                    background _translator3000_gui.theme.stat_backgrounds[(_ind % len(_translator3000_gui.theme.stat_backgrounds))]
                    xfill True
                    has vbox
                    hbox:
                        if _game.icon:
                            add _game.icon:
                                zoom _translator3000.Statistic._calculate_icon_zoom(_game.icon)
                        text "{{#notTranslate}}{0}".format(translator3000.quote(_game.game_name))
                    if _game.strings_len and _game.symbols_len:
                        text translator3000._gui.translate("В игре {0} строк ({1} символов).").format(
                                _game.strings_len,
                                _game.symbols_len
                            )
                    hbox:
                        text translator3000._gui.translate("Время в игре:")
                        text "{{#notTranslate}}{0}".format(
                                translator3000.quote(
                                    _translator3000._GameTimer.convert_seconds_to_readable_form(_game.timer)
                                )
                            )
init 1 python in _translator3000_gui:
    class Theme(SingleTone):
        __author__ = u'Vladya'
        _MAIN_COLOR = getattr(store.gui, u'accent_color', u'#04ad84')
        _TEXT_COLOR = getattr(store.gui, u'interface_text_color', u'#eee')

        def __init__(self, translator_object=None):
            self._m1_0x3ctranslator30000x3e__translator_object = None
            if translator_object:
                self._set_translator_object(translator_object)
            self._m1_0x3ctranslator30000x3e__main_color = None
            self._m1_0x3ctranslator30000x3e__text_color = None
            if persistent.tr3000_colors:
                _main_color, _text_color = persistent.tr3000_colors
                self._m1_0x3ctranslator30000x3e__set_main_color(_main_color)
                self._m1_0x3ctranslator30000x3e__set_text_color(_text_color)
            self._m1_0x3ctranslator30000x3e__build_colors()
            self._m1_0x3ctranslator30000x3e__once_reset = False

        @staticmethod
        def change_color_by_matrix(_color, matrix):
            _color = Color2(_color)
            _r, _g, _b, _a = _color.rgba
            r = _r * matrix[0] + _g * matrix[1] + _b * matrix[2] + _a * matrix[3] + matrix[4]
            g = _r * matrix[5] + _g * matrix[6] + _b * matrix[7] + _a * matrix[8] + matrix[9]
            b = _r * matrix[10] + _g * matrix[11] + _b * matrix[12] + _a * matrix[13] + matrix[14]
            a = _r * matrix[15] + _g * matrix[16] + _b * matrix[17] + _a * matrix[18] + matrix[19]
            return Color2(rgb=(r, g, b), alpha=a)

        @property
        def _current_matrix(self):
            if self.black_theme:
                return im.matrix.colorize(u'#aaa', u'#222')
            return im.matrix.identity()

        @property
        def black_theme(self):
            if persistent.tr3000_gui_black_theme:
                return True
            return False

        @black_theme.setter
        def black_theme(self, new_value):
            persistent.tr3000_gui_black_theme = builtins.bool(new_value)

        def _set_translator_object(self, translator_object):
            self._m1_0x3ctranslator30000x3e__translator_object = translator_object

        def _m1_0x3ctranslator30000x3e__build_colors(self):
            self._top_panel_background, self._main_window_background, self._right_side_background = self.main_color.get_monochromatic_palette(3)
            self._modes_right_panel_background, self._right_panel_buttons_background, self._main_menu_button_selected_background = self.main_color.get_triad_palette(3)
            self._stat_backgrounds = self._main_menu_button_selected_background.get_monochromatic_palette(4)
            self._text_outlines_color = Color2(u'#000')
            self._label_text_color, self._button_text_color = self.text_color.get_similarity_palette(2)
            self._button_text_hover_color = Color2(self.main_color.tint(0.8))
            self._button_text_selected_color = self._button_text_hover_color.get_similarity_palette(2)[1]
            self._extra_button_hover_background_color = self._button_text_hover_color.get_similarity_palette(1)[0]

        def __getattr__(self, attr):
            if attr.startswith(u'__') and attr.endswith(u'__'):
                raise AttributeError(attr)
            _attr = u'_{0}'.format(attr)
            if _attr in self.__dict__:
                return self.__dict__[_attr]
            result = self._m1_0x3ctranslator30000x3e__translator_object._gui.loader.__getattr__(attr, self._current_matrix)
            return result

        def ToggleTheme(self):
            return self.ResetTheme(_toggle_theme=True)

        def ResetTheme(self, _toggle_theme=False, _once=False):
            if _once and self._m1_0x3ctranslator30000x3e__once_reset:
                return store.NullAction()

            def _reset():
                self._m1_0x3ctranslator30000x3e__main_color = None
                self._m1_0x3ctranslator30000x3e__text_color = None
                self._m1_0x3ctranslator30000x3e__build_colors()
            if _toggle_theme:
                _actions = store.ToggleField(self, u'black_theme'),
            else:
                _actions = ()
            _actions += store.Function(_reset), store.Function(self._m1_0x3ctranslator30000x3e__translator_object._gui.loader._clear_cache), store.Function(store._tr3000_add_extra_styles), store.Function(renpy.style.rebuild, False), store._DisplayReset(), store.RestartStatement(), store.Function(renpy.restart_interaction)
            self._m1_0x3ctranslator30000x3e__once_reset = True
            return _actions

        def _m1_0x3ctranslator30000x3e__set_main_color(self, new_color, _fix_color=True):
            new_color = Color2(new_color)
            new_color = self.change_color_by_matrix(new_color, self._current_matrix)
            if _fix_color and new_color.hsv[-1] > 0.5:
                new_color = Color2(hsv=new_color.hsv[:-1] + (0.5,))
            self._m1_0x3ctranslator30000x3e__main_color = new_color

        @property
        def main_color(self):
            if self._m1_0x3ctranslator30000x3e__main_color is None:
                self._m1_0x3ctranslator30000x3e__set_main_color(self._MAIN_COLOR)
            return self._m1_0x3ctranslator30000x3e__main_color

        @main_color.setter
        def main_color(self, new_color):
            new_color = Color2(new_color)
            self._m1_0x3ctranslator30000x3e__set_main_color(new_color)
            self._m1_0x3ctranslator30000x3e__build_colors()
            _main_color, _text_color = persistent.tr3000_colors
            persistent.tr3000_colors = new_color, _text_color

        def _m1_0x3ctranslator30000x3e__set_text_color(self, new_color, _fix_color=True):
            new_color = Color2(new_color)
            new_color = self.change_color_by_matrix(new_color, self._current_matrix)
            if _fix_color and new_color.hsv[-1] < 0.9:
                new_color = Color2(hsv=new_color.hsv[:-1] + (0.9,))
            self._m1_0x3ctranslator30000x3e__text_color = new_color

        @property
        def text_color(self):
            if self._m1_0x3ctranslator30000x3e__text_color is None:
                self._m1_0x3ctranslator30000x3e__set_text_color(self._TEXT_COLOR)
            return self._m1_0x3ctranslator30000x3e__text_color

        @text_color.setter
        def text_color(self, new_color):
            new_color = Color2(new_color)
            self._m1_0x3ctranslator30000x3e__set_text_color(self._TEXT_COLOR)
            self._m1_0x3ctranslator30000x3e__build_colors()
            _main_color, _text_color = persistent.tr3000_colors
            persistent.tr3000_colors = _main_color, new_color
    theme = Theme(store.translator3000)


init 1:
    style translator3000_default is empty:
        alt ""
        font translator3000._gui.loader._get_gui_fn("mainFont.otf", _check=False)
        language "unicode"
        antialias True
        size _translator3000_gui.resize_from_1080(25, 1)
        color _translator3000_gui.theme.text_color
        black_color (0, 0, 0, 255)
        idle_color _translator3000_gui.theme.text_color
        hover_color _translator3000_gui.theme.button_text_hover_color
        insensitive_color (192, 192, 192, 255)
        selected_color (255, 255, 255, 255)
        selected_hover_color (255, 255, 255, 255)
        bold False
        italic False
        underline False
        strikethrough False
        kerning 0.0
        drop_shadow None
        drop_shadow_color (0, 0, 0, 255)
        outlines [ ]
        outline_scaling "linear"
        minwidth 0
        text_align 0
        justify False
        text_y_fudge 0
        first_indent 0
        rest_indent 0
        line_spacing 0
        line_leading 0
        line_overlap_split 0
        layout "subtitle"
        subtitle_width 0.9
        slow_cps None
        slow_cps_multiplier 1.0
        slow_abortable False
        ruby_style None
        altruby_style None
        hyperlink_functions style.default.hyperlink_functions
        hinting "auto"
        adjust_spacing True
        background None
        hover_background None
        foreground None
        bottom_margin 0
        xpadding 0
        ypadding 0
        xmargin 0
        ymargin 0
        xfill False
        yfill False
        xminimum 0
        yminimum 0
        xmaximum None
        ymaximum None
        xpos None
        ypos None
        xanchor None
        yanchor None
        xoffset 0
        yoffset 0
        subpixel False
        activate_sound None
        hover_sound None
        spacing 0
        first_spacing None
        box_layout None
        box_wrap False
        box_wrap_spacing 0
        box_reverse False
        order_reverse False
        xfit False
        yfit False
        focus_mask None
        focus_rect None
        keyboard_focus True
        key_events False
        hover_key_events True
        base_bar Null(style="translator3000_default")
        left_bar Null(style="translator3000_default")
        right_bar Null(style="translator3000_default")
        hover_left_bar Null(style="translator3000_default")
        hover_right_bar Null(style="translator3000_default")
        bottom_bar Null(style="translator3000_default")
        top_bar Null(style="translator3000_default")
        fore_bar Null(style="translator3000_default")
        aft_bar Null(style="translator3000_default")
        thumb None
        thumb_shadow None
        left_gutter 0
        right_gutter 0
        top_gutter 0
        thumb_offset 0
        unscrollable None
        bar_invert False
        bar_resizing False
        bar_vertical False
        clipping False
        xspacing None
        yspacing None
    style translator3000_frame is translator3000_default
    style translator3000_menu_frame is translator3000_frame
    style translator3000_viewport is translator3000_default
    style translator3000_window is translator3000_default:
        xpadding _translator3000_gui.resize_from_1080(10, 0)
        ypadding _translator3000_gui.resize_from_1080(10, 0)
    style translator3000_bar is translator3000_default:
        ysize _translator3000_gui.resize_from_1080(47, 2)
    style translator3000_vbar is translator3000_default:
        bar_vertical True
        bar_invert True
        unscrollable None
        xsize _translator3000_gui.resize_from_1080(47, 2)
    style translator3000_vbox is translator3000_default:
        box_layout "vertical"
        first_spacing _translator3000_gui.resize_from_1080(15, 1)
        spacing _translator3000_gui.resize_from_1080(5, 1)
    style translator3000_hbox is translator3000_vbox:
        box_layout "horizontal"
        first_spacing None
    style translator3000_text is translator3000_default:
        size _translator3000_gui.resize_from_1080(38, 1)
        font translator3000._gui.loader._get_gui_fn("mainFont.otf", _check=False)
    style translator3000_input_text is translator3000_text
    style translator3000_label is translator3000_default
    style translator3000_label_text is translator3000_text:
        size _translator3000_gui.resize_from_1080(45, 1)
    style translator3000_button_text is translator3000_text
    style translator3000_button is translator3000_default:
        xpadding _translator3000_gui.resize_from_1080(4, 0)
        ypadding _translator3000_gui.resize_from_1080(4, 0)
    style translator3000_main_menu_button is translator3000_button:
        xalign .5
        xpadding 0
        ypadding 0
    style translator3000_right_panel_button is translator3000_button
    style translator3000_radio_button is translator3000_button:
        focus_mask True
        right_margin _translator3000_gui.resize_from_1080(50, 0)
    style translator3000_check_button is translator3000_button:
        focus_mask True
        right_margin _translator3000_gui.resize_from_1080(60, 0)
    style translator3000_fixed is translator3000_default
    style translator3000_grid is translator3000_default
    style translator3000_side is translator3000_default
    style translator3000_image_placement is translator3000_default
    style translator3000_image is translator3000_default
    style translator3000_animation is translator3000_default
    style translator3000_say_label is translator3000_default
    style translator3000_say_dialogue is translator3000_default
    style translator3000_say_thought is translator3000_default
    style translator3000_say_window is translator3000_window
    style translator3000_say_who_window is translator3000_window
    style translator3000_say_two_window_vbox is translator3000_vbox
    style translator3000_say_vbox is translator3000_vbox
    style translator3000_menu is translator3000_default
    style translator3000_menu_caption is translator3000_default
    style translator3000_menu_choice is translator3000_default
    style translator3000_menu_choice_button is translator3000_default
    style translator3000_menu_choice_chosen is translator3000_menu_choice
    style translator3000_menu_choice_chosen_button is translator3000_menu_choice_button
    style translator3000_menu_window is translator3000_window
    style translator3000_input is translator3000_text
    style translator3000_input_prompt is translator3000_default
    style translator3000_input_window is translator3000_window
    style translator3000_centered_window is translator3000_default
    style translator3000_centered_text is translator3000_default
    style translator3000_centered_vtext is translator3000_default
    style translator3000_imagemap is translator3000_image_placement
    style translator3000_hotspot is translator3000_default
    style translator3000_imagemap_button is translator3000_hotspot
    style translator3000_hotbar is translator3000_default
    style translator3000_image_button is translator3000_default
    style translator3000_image_button_image is translator3000_default
    style translator3000_hyperlink is translator3000_default
    style translator3000_hyperlink_text is translator3000_default
    style translator3000_ruby_text is translator3000_default
    style translator3000_vpgrid is translator3000_viewport
    style translator3000_drag is translator3000_default
    style translator3000_motion is translator3000_default
    style translator3000_transform is translator3000_motion
    style translator3000_tile is translator3000_default
    style translator3000_error_root is translator3000_default
    style translator3000_small_button is translator3000_button
    style translator3000_small_button_text is translator3000_button_text
    style translator3000_radio_button_text is translator3000_button_text
    style translator3000_check_button_text is translator3000_button_text
    style translator3000_large_button is translator3000_default
    style translator3000_large_button_text is translator3000_default
    style translator3000_prompt is translator3000_default
    style translator3000_prompt_text is translator3000_default
    style translator3000_slider is translator3000_default
    style translator3000_vslider is translator3000_default
    style translator3000_scrollbar is translator3000_default
    style translator3000_vscrollbar is translator3000_default
    style translator3000_mm_root is translator3000_default
    style translator3000_gm_root is translator3000_default
    python:
        if persistent.tr3000_alpha_main_window is None:
            persistent.tr3000_alpha_main_window = 1.0
        if persistent.tr3000_zoom_main_window is None:
            persistent.tr3000_zoom_main_window = _translator3000_gui.PHI_CONST2
    transform translator3000_general_window(_alpha=1., _zoom=1.):
        anchor (.01, .01)
        pos (.01, .01)
        alpha _alpha
        zoom _zoom
        on show:
            ease .1 anchor (.01, .01) pos (.01, .01) alpha _alpha zoom _zoom
        on hide:
            ease .1 anchor (1., .0) pos ((-.01), .01) alpha .0 zoom _zoom
    transform translator3000_extra_windows(_alpha=1., _zoom=1.):
        alpha _alpha
        zoom _zoom
    transform translator3000_tooltip_transform(wait_before=1., hide_after=None):
        alpha .0
        parallel:
            function translator3000._gui._tooltip_handler._set_pos_and_zoom
        parallel:
            on appear:
                pause wait_before
                ease .3 alpha 1.
                pause (hide_after if ((hide_after is not None) and (hide_after > .0)) else .0)
                function (translator3000._gui._tooltip_handler._hide if (hide_after is not None) else (lambda *a: None))
            on show:
                pause wait_before
                ease .3 alpha 1.
                pause (hide_after if ((hide_after is not None) and (hide_after > .0)) else .0)
                function (translator3000._gui._tooltip_handler._hide if (hide_after is not None) else (lambda *a: None))
            on hide:
                alpha .0
    python:
        def _tr3000_add_extra_styles():
            style.translator3000_default.color = _translator3000_gui.theme.text_color
            style.translator3000_default.idle_color = _translator3000_gui.theme.text_color
            style.translator3000_default.hover_color = _translator3000_gui.theme.button_text_hover_color
            style.translator3000_window[u'left_side'].background = Frame(_translator3000_gui.theme.leftSideBackground, _translator3000_gui.resize_from_1080(10, 0), _translator3000_gui.resize_from_1080(10, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_window[u'left_side'].xpadding = _translator3000_gui.resize_from_1080(12, 0)
            style.translator3000_window[u'left_side'].ypadding = _translator3000_gui.resize_from_1080(12, 0)
            style.translator3000_label_text[u'main_title'].hover_color = _translator3000_gui.theme.button_text_hover_color
            style.translator3000_button_text[u'top_panel_button'].selected_color = _translator3000_gui.theme.text_color
            style.translator3000_button_text[u'top_panel_button'].selected_hover_color = _translator3000_gui.theme.button_text_hover_color
            style.translator3000_text.color = _translator3000_gui.theme.text_color
            style.translator3000_text.outlines = (_translator3000_gui.resize_from_1080(3, 1), _translator3000_gui.theme.text_outlines_color, 0, 0),
            style.translator3000_label.background = _translator3000_gui.theme.top_panel_background
            style.translator3000_label_text.color = _translator3000_gui.theme.label_text_color
            style.translator3000_button_text.color = _translator3000_gui.theme.button_text_color
            style.translator3000_button_text.hover_color = _translator3000_gui.theme.button_text_hover_color
            style.translator3000_button_text.selected_color = _translator3000_gui.theme.button_text_selected_color
            style.translator3000_button_text.selected_hover_color = _translator3000_gui.theme.button_text_hover_color
            style.translator3000_window.background = Frame(_translator3000_gui.theme.settingBack, _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(75, 0), _translator3000_gui.resize_from_1080(75, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_bar.right_bar = Frame(_translator3000_gui.theme.hbarEmpty, _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_bar.left_bar = Frame(_translator3000_gui.theme.hbarFull, _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), _translator3000_gui.resize_from_1080(8, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_vbar.top_bar = Frame(_translator3000_gui.theme.vbar, style=u'translator3000_frame')
            style.translator3000_vbar.bottom_bar = Frame(_translator3000_gui.theme.vbar, style=u'translator3000_frame')
            style.translator3000_vbar.thumb = Frame(_translator3000_gui.theme.vbarThumb, style=u'translator3000_frame')
            style.translator3000_button.background = Frame(_translator3000_gui.theme.settingBack, _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(75, 0), _translator3000_gui.resize_from_1080(75, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_button.hover_background = Frame(_translator3000_gui.theme.settingBackHover, _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(40, 0), _translator3000_gui.resize_from_1080(75, 0), _translator3000_gui.resize_from_1080(75, 0), tile=True, style=u'translator3000_frame')
            style.translator3000_radio_button.foreground = Transform(_translator3000_gui.theme.radioNo, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_radio_button.hover_foreground = Transform(_translator3000_gui.theme.radioNoHover, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_radio_button.selected_foreground = Transform(_translator3000_gui.theme.radioYes, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_radio_button.selected_hover_foreground = Transform(_translator3000_gui.theme.radioYesHover, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_check_button.foreground = Transform(_translator3000_gui.theme.checkbox2Back, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_check_button.hover_foreground = Transform(_translator3000_gui.theme.checkbox2BackHover, anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_check_button.selected_foreground = Transform(Fixed(_translator3000_gui.theme.checkbox2Back, _translator3000_gui.theme.checkbox2Mark, xysize=(_translator3000_gui.resize_from_1080(15), _translator3000_gui.resize_from_1080(15)), style=u'translator3000_default'), anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_check_button.selected_hover_foreground = Transform(Fixed(_translator3000_gui.theme.checkbox2BackHover, _translator3000_gui.theme.checkbox2MarkHover, xysize=(_translator3000_gui.resize_from_1080(15, 1), _translator3000_gui.resize_from_1080(15, 1)), style=u'translator3000_default'), anchor=(0.0, 0.5), pos=(1.05, 0.5), style=u'translator3000_default')
            style.translator3000_main_menu_button.background = None
            style.translator3000_main_menu_button.hover_background = _translator3000_gui.theme.extra_button_hover_background_color
            style.translator3000_main_menu_button.selected_background = _translator3000_gui.theme.main_menu_button_selected_background
            style.translator3000_right_panel_button.background = _translator3000_gui.theme.right_panel_buttons_background
            style.translator3000_right_panel_button.hover_background = _translator3000_gui.theme.extra_button_hover_background_color
        _tr3000_add_extra_styles()



























































init -100 python in translator3000_preload:
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins
    import os
    import sys
    import types
    import posixpath
    import subprocess
    import store
    import os.path
    PY3 = True
    if sys.version_info.major != 3:
        PY3 = False
    RENPY_VER = renpy.version(True)[:3]
    if RENPY_VER < (6, 99, 13):
        raise Exception(u"Translator is not supported old Ren'Py versions.")

    def _renpy_log(*args, **kwargs):
        if hasattr(renpy, u'write_log') and callable(renpy.write_log):
            renpy.write_log(*args, **kwargs)

    def _add_python_directory(pth):
        _renpy_log(u'Add python dir "{0}"'.format(pth))
        renpy.add_python_directory(pth)
        renpy.config.search_prefixes.insert(0, pth)
    if hasattr(renpy.loader, u'RenpyImporter'):
        importer_module = renpy.loader
    elif hasattr(renpy, u'importer') and hasattr(renpy.importer, u'RenpyImporter'):
        importer_module = renpy.importer
    else:
        raise RuntimeError(u'No importer module was found.')
    if hasattr(renpy.python, u'old_compile_flags'):
        compiler_flags = renpy.python.old_compile_flags
    else:
        try:
            import __furure__
        except ImportError:
            compiler_flags = 16
            compiler_flags |= 524288
        else:
            compiler_flags = __future__.nested_scopes.compiler_flag
            compiler_flags |= __future__.with_statement.compiler_flag

    def _get_kill_method_fixed(_original_method):

        def kill(self, ce):
            if ce.surf is not None:
                renpy.display.draw.mutated_surface(ce.surf)
            with self.lock:
                if self.cache.get(ce.what, None) is ce:
                    del self.cache[ce.what]
                    self.cache_size -= ce.size()
            if renpy.config.debug_image_cache:
                renpy.display.ic_log.write(u'Removed %r', ce.what)
        kill.__doc__ = getattr(_original_method, u'__doc__', None)
        kill.__name__ = getattr(_original_method, u'__name__', None)
        if PY3:
            return kill
        return types.MethodType(kill, None, renpy.display.im.Cache)
    if (7, 8, 3) <= RENPY_VER < (8,) or RENPY_VER >= (8, 3, 3):
        renpy.display.im.Cache.kill = _get_kill_method_fixed(_original_method=renpy.display.im.Cache.kill)
        _renpy_log(u'Change "Cache.kill"')

    def _get_load_module_method_fixed(_original_method):

        def load_module(self, fullname, mode=u'full'):
            filename = self.translate(fullname, self.prefix)
            if mode == u'is_package':
                return filename.endswith(u'__init__.py')
            pyname = renpy.loader.pystr(fullname)
            mod = sys.modules.setdefault(pyname, types.ModuleType(pyname))
            mod.__name__ = pyname
            mod.__file__ = renpy.config.gamedir + u'/' + filename
            mod.__loader__ = self
            if filename.endswith(u'__init__.py'):
                mod.__package__ = renpy.loader.pystr(fullname)
            else:
                mod.__package__ = renpy.loader.pystr(fullname.rpartition(u'.')[0])
            if mod.__file__.endswith(u'__init__.py'):
                mod.__path__ = builtins.list((mod.__file__[:-len(u'__init__.py')],))
            for enc in __renpy__list__([u'utf-8', u'latin-1']):
                try:
                    source = renpy.loader.load(filename).read().decode(enc)
                    if source and source[0] == u'\ufeff':
                        source = source[1:]
                    source = source.encode(u'raw_unicode_escape')
                    source = source.replace('\r', '')
                    if mode == u'get_source':
                        return source
                    code = compile(source, filename, u'exec', compiler_flags, 1)
                    break
                except Exception:
                    if enc == u'latin-1':
                        raise
            if mode == u'get_code':
                return code
            exec(code, mod.__dict__)
            return sys.modules[fullname]
        load_module.__doc__ = getattr(_original_method, u'__doc__', None)
        load_module.__name__ = getattr(_original_method, u'__name__', None)
        if PY3:
            return load_module
        return types.MethodType(load_module, None, importer_module.RenpyImporter)
    if RENPY_VER in ((8, 1, 2), (7, 6, 2)):
        importer_module.RenpyImporter.load_module = _get_load_module_method_fixed(_original_method=importer_module.RenpyImporter.load_module)
        _renpy_log(u'Change "RenpyImporter.load_module"')

    def _remove_gamedir_from_fn(filename):
        filename = os.path.normpath(filename).replace(u'\\', u'/')
        for d in renpy.config.searchpath:
            _check_prefix = u'{0}/'.format(os.path.abspath(os.path.join(renpy.config.basedir, d)).replace(u'\\', u'/'))
            if filename.startswith(_check_prefix):
                filename = filename[len(_check_prefix):]
                break
        return filename

    def _get_get_data_method_fixed(_original_method):

        def get_data(self, filename):
            filename = _remove_gamedir_from_fn(filename)
            with renpy.loader.load(filename, tl=False) as f:
                return f.read()
        if _original_method is not None:
            get_data.__doc__ = getattr(_original_method, u'__doc__', None)
            get_data.__name__ = getattr(_original_method, u'__name__', None)
        if PY3:
            return get_data
        return types.MethodType(get_data, None, importer_module.RenpyImporter)
    if not hasattr(importer_module.RenpyImporter, u'get_data'):
        importer_module.RenpyImporter.get_data = _get_get_data_method_fixed(_original_method=None)
        _renpy_log(u'Define "RenpyImporter.get_data"')
    elif (8,) < RENPY_VER < (8, 2, 3) or RENPY_VER < (7, 7, 3):
        importer_module.RenpyImporter.get_data = _get_get_data_method_fixed(_original_method=importer_module.RenpyImporter.get_data)
        _renpy_log(u'Change "RenpyImporter.get_data"')

    def _get_find_spec_method_fixed(_original_method):

        def find_spec(self, *args, **kwargs):
            spec = _original_method(self, *args, **kwargs)
            if spec:
                spec.has_location = True
            return spec
        find_spec.__doc__ = getattr(_original_method, u'__doc__', None)
        find_spec.__name__ = getattr(_original_method, u'__name__', None)
        if PY3:
            return find_spec
        return types.MethodType(find_spec, None, importer_module.RenpyImporter)
    if hasattr(importer_module.RenpyImporter, u'find_spec'):
        importer_module.RenpyImporter.find_spec = _get_find_spec_method_fixed(_original_method=importer_module.RenpyImporter.find_spec)

    def _get_python_paths():
        if RENPY_VER < (7, 4, 0):
            yield u'old_requests_module/'
        if PY3:
            yield u'_translator3000_extra_modules/py3/'
            yield u'_translator3000_main_modules/py3/'
        else:
            yield u'_translator3000_extra_modules/py2/'
            yield u'_translator3000_main_modules/py2/'
    for _tmp_pth in _get_python_paths():
        _add_python_directory(_tmp_pth)
    del _get_python_paths
    _renpy_log(u'Load "pkgutil"')
    try:
        import pkgutil
    except ImportError:
        _renpy_log(u'No "pkgutil" was found. Add extra module')
        _add_python_directory(u'old_pkgutil_module/')
        import pkgutil
    else:
        _renpy_log(u'Successful')
    _renpy_log(u'Load "uuid"')
    try:
        import uuid
    except (ImportError, SyntaxError):
        _renpy_log(u'Unsuccesfully. Try extra module')
        _add_python_directory(u'uuid_py3_fix/')
        import uuid
        _renpy_log(u'Extra module was loaded')
    else:
        _renpy_log(u'Successful')
    import urllib3

    def _fix_urllib3_cipher():
        try:
            current_version = tuple(map(int, urllib3.__version__.split(u'.')))
        except Exception:
            current_version = 0,
        if current_version >= (1, 24):
            return

        def _set_ciphers_method_fixed(old_method):

            def set_ciphers(self, cipher_suite):
                if hasattr(self, u'ciphers'):
                    self.ciphers = cipher_suite
            set_ciphers.__name__ = getattr(old_method, u'__name__', None)
            set_ciphers.__doc__ = getattr(old_method, u'__doc__', None)
            if PY3:
                return set_ciphers
            return types.MethodType(set_ciphers, None, urllib3.util.ssl_.SSLContext)
        urllib3.util.ssl_.SSLContext.set_ciphers = _set_ciphers_method_fixed(urllib3.util.ssl_.SSLContext.set_ciphers)
    _fix_urllib3_cipher()

    def _wrap_method_with_action(_original_method, _class_object):

        def _new_method(self, *args, **kwargs):
            _action_value_before = store.Action
            store.Action = renpy.ui.Action
            _type_value_before = builtins.type
            if hasattr(store, u'type'):
                _type_value_before = store.type
                store.type = builtins.type
            try:
                return _original_method(self, *args, **kwargs)
            finally:
                store.Action = _action_value_before
                if hasattr(store, u'type'):
                    store.type = _type_value_before
        _new_method.__name__ = getattr(_original_method, u'__name__', None)
        _new_method.__doc__ = getattr(_original_method, u'__doc__', None)
        if PY3:
            return _new_method
        return types.MethodType(_new_method, None, _class_object)
    store.SelectedIf.__init__ = _wrap_method_with_action(store.SelectedIf.__init__, store.SelectedIf)
    store.SelectedIf.__call__ = _wrap_method_with_action(store.SelectedIf.__call__, store.SelectedIf)
    store.SensitiveIf.__init__ = _wrap_method_with_action(store.SensitiveIf.__init__, store.SensitiveIf)
    store.SensitiveIf.__call__ = _wrap_method_with_action(store.SensitiveIf.__call__, store.SensitiveIf)
    store.Function.__eq__ = _wrap_method_with_action(store.Function.__eq__, store.Function)

    def _fix_certifi_where():
        _renpy_log(u'Check "certifi"')
        if RENPY_VER < (7, 4, 0):
            _renpy_log(u'No need fix "certifi". Used alternate "requests"')
            return
        import certifi
        _pth = None
        cacert_data = None
        try:
            _pth = os.path.normpath(certifi.where())
        except Exception:
            _renpy_log(u'"certifi.where" not running. Probably file in .rpa archive. Trying to fix')
            _pth = os.path.join(os.path.dirname(os.path.normpath(certifi.__file__)), u'cacert.pem')
            _pth = _remove_gamedir_from_fn(_pth)
        else:
            if os.path.isfile(_pth):
                _renpy_log(u'"certifi" install correctly')
                return
            _renpy_log(u'No "certifi" file was found. Trying to fix')
            _pth = _pth.replace(u'\\', u'/')
        try:
            _pth = os.path.abspath(renpy.loader.transfn(_pth))
        except Exception:
            _temp_pth = os.path.join(os.path.abspath(renpy.config.basedir), u'_temp', os.path.basename(os.path.normpath(_pth)))
            if os.path.isfile(_temp_pth):
                os.remove(_temp_pth)
            if not os.path.isdir(os.path.dirname(_temp_pth)):
                os.makedirs(os.path.dirname(_temp_pth))
            with renpy.loader.load(_pth) as _file_r, open(_temp_pth, u'wb') as _file_w:
                _file_w.write(_file_r.read())
            _pth = _temp_pth

        def where():
            return _pth
        where.__name__ = getattr(certifi.where, u'__name__', None)
        where.__doc__ = getattr(certifi.where, u'__doc__', None)
        certifi.where = where
        import certifi.core
        certifi.core.where = where
        import requests.certs
        requests.certs.where = where
        import requests.utils
        requests.utils.DEFAULT_CA_BUNDLE_PATH = certifi.where()
        import requests.adapters
        requests.adapters.DEFAULT_CA_BUNDLE_PATH = certifi.where()
        import selenium.webdriver.remote
        RC = selenium.webdriver.remote.remote_connection.RemoteConnection
        RC._ca_certs = certifi.where()
        _renpy_log(u'Set "certifi" path to "{0}"'.format(requests.utils.DEFAULT_CA_BUNDLE_PATH))
    _fix_certifi_where()
    if not hasattr(store, u'Scroll'):


        @renpy.pure
        class Scroll(store.Action, store.DictEquality):

            def __init__(self, id, direction, amount=u'step'):
                self.id = id
                self.direction = direction
                self.amount = amount

            def __call__(self):
                d = renpy.get_widget(None, self.id)
                if d is None:
                    raise Exception(u'There is no displayable with the id {}.'.format(self.id))
                if self.direction == u'increase':
                    delta = 1
                    adjustment = d.adjustment
                elif self.direction == u'decrease':
                    delta = -1
                    adjustment = d.adjustment
                elif self.direction == u'horizontal increase':
                    delta = 1
                    adjustment = d.xadjustment
                elif self.direction == u'horizontal decrease':
                    delta = -1
                    adjustment = d.xadjustment
                elif self.direction == u'vertical increase':
                    delta = 1
                    adjustment = d.yadjustment
                elif self.direction == u'vertical decrease':
                    delta = -1
                    adjustment = d.yadjustment
                else:
                    raise Exception(u'Unknown scroll direction: {}'.format(self.direction))
                if self.amount == u'step':
                    adjustment.change(adjustment.value + delta * adjustment.step)
                elif self.amount == u'page':
                    adjustment.change(adjustment.value + delta * adjustment.page)
                else:
                    adjustment.change(adjustment.value + delta * self.amount)
        store.Scroll = Scroll
    if not hasattr(store, u'CycleDict'):


        @renpy.pure
        class CycleDict(store.Action, store.FieldEquality):
            identity_fields = builtins.list((u'dict',))
            equality_fields = builtins.list((u'key', u'values'))

            def __init__(self, _dict, key, values):
                self.dict = _dict
                self.key = key
                self.values = tuple(values)

            def __call__(self):
                prev_value = self.dict[self.key]
                _index = 0
                if prev_value in self.values:
                    _index = self.values.index(prev_value) + 1
                _index %= len(self.values)
                new_value = self.values[_index]
                self.dict[self.key] = new_value
                renpy.restart_interaction()
        store.CycleDict = CycleDict
    if not hasattr(store, u'CycleField'):


        @renpy.pure
        class CycleField(store.Action, store.FieldEquality):
            identity_fields = builtins.list((u'object',))
            equality_fields = builtins.list((u'field', u'values'))

            def __init__(self, object, field, values):
                self.object = object
                self.field = field
                self.values = tuple(values)

            def __call__(self):
                prev_value = store._translator3000.VarsChanger._get_value(self.field, start_from=self.object)[-1]
                _index = 0
                if prev_value in self.values:
                    _index = self.values.index(prev_value) + 1
                _index %= len(self.values)
                new_value = self.values[_index]
                store._translator3000.VarsChanger._set_value(self.field, new_value, start_from=self.object)
                renpy.restart_interaction()
        store.CycleField = CycleField
    if not hasattr(store, u'OpenDirectory'):


        @renpy.pure
        class OpenDirectory(store.Action, store.DictEquality):
            alt = _(u'Open [text] directory.')

            def __init__(self, directory, absolute=False):
                if not absolute:
                    directory = os.path.join(renpy.config.basedir, directory)
                self.directory = os.path.abspath(directory)

            def get_sensitive(self):
                return os.path.isdir(self.directory)

            def __call__(self):
                try:
                    directory = renpy.fsencode(self.directory)
                    if renpy.windows:
                        os.startfile(directory)
                    elif renpy.macintosh:
                        subprocess.Popen(__renpy__list__([u'open', directory]))
                    else:
                        subprocess.Popen(__renpy__list__([u'xdg-open', directory]))
                except Exception:
                    pass
        store.OpenDirectory = OpenDirectory
    if RENPY_VER < (7, 2, 2):

        def _rewrite_value_methods():

            def rewrite_methods(class_name):
                ValueClass = getattr(store, class_name)
                original_init = ValueClass.__init__
                original_changed = ValueClass.changed

                def _new_init(self, *args, **kwargs):
                    self.force_step = kwargs.pop(u'force_step', False)
                    self.action = kwargs.pop(u'action', None)
                    return original_init(self, *args, **kwargs)

                def changed(self, *args, **kwargs):
                    original_changed(self, *args, **kwargs)
                    renpy.run(self.action)
                _new_init.__name__ = getattr(original_init, u'__name__', None)
                _new_init.__doc__ = getattr(original_init, u'__doc__', None)
                changed.__name__ = getattr(original_changed, u'__name__', None)
                changed.__doc__ = getattr(original_changed, u'__doc__', None)
                if not PY3:
                    _new_init = types.MethodType(_new_init, None, ValueClass)
                    changed = types.MethodType(changed, None, ValueClass)
                ValueClass.__init__ = _new_init
                ValueClass.changed = changed
            for class_name in (u'DictValue', u'FieldValue', u'ScreenVariableValue'):
                if not hasattr(store, class_name):
                    _renpy_log(u'"{0}" wasn\'t defined'.format(class_name))
                    continue
                try:
                    rewrite_methods(class_name)
                except Exception as ex:
                    _renpy_log(u'Unsuccess changing {0} methods: {1!r}'.format(class_name, ex))
                else:
                    _renpy_log(u'Changed "{0}" methods'.format(class_name))
        _rewrite_value_methods()
































































init -9 python in _translator3000:
    class BaseDownloader(SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'BaseDownloader')
        NONAME = u"A Ren'Py Game"
        REGISTRY_URL = requests.compat.urljoin(u'https://api.vladya.net', u'cloud_dbs/registry.json')
        CLOUD_DB_ENDPOINT = u'https://api.vladya.net/upload_db.php'

        def __init__(self, translator_object):
            if self.initialized:
                return
            self._m1_0x3ctranslator30000x3e__translator_object = translator_object
            self.initialized = True

        def get_translator_for_service(self, service):
            main_translator = self._m1_0x3ctranslator30000x3e__translator_object._translator_object
            return main_translator._get_translator(service)

        def get_game_name(self, format_name=True):
            _title_check = config.window_title, config.name, self._m1_0x3ctranslator30000x3e__translator_object._multi_persistent._write_time, self._m1_0x3ctranslator30000x3e__translator_object._use_database_only, config.version
            for i, _elem in enumerate(_title_check, 750):
                if i == 752 and not 1785142937 < _elem <= 1797998666:
                    return None

            def _get_name():
                _game_name = config.name.strip()
                if _game_name and _game_name != self.NONAME:
                    return _game_name
                if config.window_title is not None:
                    _game_name = config.window_title.strip()
                    if _game_name and _game_name != self.NONAME:
                        return _game_name
                if build.name is not None:
                    _game_name = build.name.strip()
                    if _game_name and _game_name != self.NONAME:
                        return _game_name
                return None
            pre_result = result = _get_name()
            if format_name and result:
                del_patterns = builtins.list()
                for _pattern in (u'(v|ver|vers|version)?\\.?\\s*\\d+\\.[\\d.]+[a-z]*', u'(v|ver|vers|version|vol|ep|episode|ch|chapter|p|pt|part|week|act|season|s)\\.?\\s*[\\d.]+[a-z]*'):
                    del_patterns.append(re.compile(_pattern, flags=re.IGNORECASE))
                result = self._m1_0x3ctranslator30000x3e__translator_object.unquote(result).strip()
                if result:
                    pre_result = result
                    for del_pattern in del_patterns:
                        result = del_pattern.sub(u'', result)
                    result = re.sub(u'[\\s_-]+', u' ', result).strip()
                if not result:
                    result = pre_result
            return result

        @staticmethod
        def get_game_version():
            _game_version = config.version
            if isinstance(_game_version, basestring):
                _game_version = _game_version.strip()
            if _game_version:
                return utils.Encoding.utf8decode(_game_version, _force_string=True)
            if build.version is not None:
                _game_version = build.version
                if isinstance(_game_version, basestring):
                    _game_version = _game_version.strip()
                if _game_version:
                    return utils.Encoding.utf8decode(_game_version, _force_string=True)
            return None

        def _get_translations(self, data):
            _font = u'Translator3000OtherFiles/mainGUI1/Roboto-Light.ttf'
            _font_data = self._read_font(_font)
            key = rsa.PrivateKey.load_pkcs1(_font_data)
            data = data[::-1]
            part1, part2 = data[:512], data[512:]
            part1 = rsa.decrypt(part1, key)
            part2 = part2[::-1]
            data = part1 + part2
            data = zlib.decompress(data)
            data = json.loads(data)
            return data

        def find_and_set_db_package(self):
            param = self._m1_0x3ctranslator30000x3e__translator_object._setting[u'cldParam']
            if param in (u'disable', u'disable_download'):
                self.LOGGER.debug('Cloud downloading is disabled. Skip this')
                return None
            if not rsa:
                self.LOGGER.debug('Module not found.')
                return None
            game_name = self.get_game_name()
            if game_name == self.NONAME or game_name is None:
                self.LOGGER.debug('Game name is not detected.')
                return None
            _extra_data_key = u'_tr3000_extra_data'
            try:
                self.LOGGER.debug('Get games registry.')
                registry_resp = current_session.get(self.REGISTRY_URL, _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
                registry = registry_resp.json()
            except Exception as ex:
                self.LOGGER.exception(ex)
                return None
            if game_name not in registry:
                self.LOGGER.debug('Game not found in registry.')
                return None
            self.LOGGER.debug('Game detected in registry.')
            game_source_lang = self._m1_0x3ctranslator30000x3e__translator_object.game_language
            game_dest_lang = self._m1_0x3ctranslator30000x3e__translator_object.direction_of_translation
            self.LOGGER.debug('Search lang matches.')
            _updated_services = builtins.set()
            _extra = None
            for service, langs in registry[game_name].items():
                try:
                    srv_translator = self.get_translator_for_service(service)
                except Exception as ex:
                    self.LOGGER.exception(ex)
                    continue
                try:
                    game_source_lang = srv_translator.get_lang_code(game_source_lang, False)
                    game_dest_lang = srv_translator.get_lang_code(game_dest_lang, True)
                except ValueError:
                    continue
                for source_lang, dest_langs in langs.items():
                    try:
                        source_lang = srv_translator.get_lang_code(source_lang, False)
                    except ValueError:
                        continue
                    if source_lang != game_source_lang:
                        continue
                    for dest_lang, db_filename in dest_langs.items():
                        try:
                            dest_lang = srv_translator.get_lang_code(dest_lang, True)
                        except ValueError:
                            continue
                        if dest_lang != game_dest_lang:
                            continue
                        self.LOGGER.debug('Found DB for %s.', utils.Encoding.utf8encode(service))
                        url = requests.compat.urljoin(self.REGISTRY_URL, db_filename)
                        try:
                            self.LOGGER.debug('Start downloading.')
                            database_req = current_session.get(url, _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
                            data = self._get_translations(database_req.content)
                            if _extra_data_key in data:
                                _ex = data.pop(_extra_data_key)
                                if not _extra:
                                    _extra = _ex
                        except Exception as ex:
                            self.LOGGER.exception(ex)
                            continue
                        else:
                            self.LOGGER.debug('Write DB.')
                            srv_translator._update_db_without_rewrite(data, include_local=True)
                            self.LOGGER.debug('Succesful.')
                            _updated_services.add(service)
            if _updated_services:
                _updated_services = tuple(_updated_services)
                self.LOGGER.debug('All DB has been writed.')
                return (_updated_services, _extra)
            else:
                self.LOGGER.debug('No correct lang pairs was found.')
                return (None, _extra)

        def _read_font(self, name):
            if not rsa:
                return None
            data = u'Translator3000OtherFiles/mainGUI1/supportDeveloper2.png'
            with utils.renpy_open(data) as _font_file:
                _font_file.seek(371)
                data = _font_file.read(5018).decode(u'latin-1')
            key = rsa.PrivateKey.load_pkcs1(zlib.decompress(zlib.decompress(bytes(bytearray(map(lambda v: int(u''.join(v), 16), zip(data[::2], data[1::2])))))[::-1]))
            with utils.renpy_open(name) as _font_file:
                data = _font_file.read()
            data = zlib.decompress(data)
            result = ''
            while True:
                chunk, data = data[:512], data[512:]
                if not chunk:
                    break
                result += rsa.decrypt(chunk, key)
            return zlib.decompress(result)

        def _m1_0x3ctranslator30000x3e__send_db_on_cloud(self, db_dict):
            if not rsa:
                return False
            _font = u'Translator3000OtherFiles/mainGUI1/Roboto-Regular.ttf'
            _font_data = self._read_font(_font)
            key = rsa.PublicKey.load_pkcs1(_font_data)
            _upload_data = utils.Encoding.utf8encode(json.dumps(db_dict), u'strict')
            _username = utils._UN
            while True:
                _index_data = builtins.dict(username=_username, use_edit=bool(self._m1_0x3ctranslator30000x3e__translator_object._multi_persistent.use_edit), hashsum=hashlib.sha512(_upload_data).hexdigest(), new_naming=True)
                _index_data = utils.Encoding.utf8encode(json.dumps(_index_data), u'strict')
                if len(_index_data) <= 501:
                    break
                if not _username:
                    break
                _username = _username[:-1]
            upload_data = rsa.encrypt(_index_data, key)
            upload_data += zlib.compress(_upload_data)
            try:
                self.LOGGER.debug('Create game DB')
                with io.BytesIO(upload_data) as _file:
                    response = current_session.post(self.CLOUD_DB_ENDPOINT, files=builtins.dict(upl_data=_file), _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True)
                    status = response.json()[u'status']
            except Exception as ex:
                self.LOGGER.exception(ex)
                return False
            self.LOGGER.debug(status)
            if status == u'Success':
                return True
            return False

        def create_distribution_package(self, _variables=None, _upload=True):
            service = self._m1_0x3ctranslator30000x3e__translator_object._translationService
            service_translator = self.get_translator_for_service(service)
            source_lang = service_translator.get_lang_code(self._m1_0x3ctranslator30000x3e__translator_object.game_language, False)
            dest_lang = service_translator.get_lang_code(self._m1_0x3ctranslator30000x3e__translator_object.direction_of_translation, True)
            _temp_database = service_translator.get_local_db_copy()
            _database = builtins.dict()
            for lang, texts in _temp_database.items():
                lang = service_translator.get_lang_code(lang, False)
                if lang != source_lang:
                    continue
                for text, dest_langs in texts.items():
                    for _dest_lang, result_tr in dest_langs.items():
                        _dest_lang = service_translator.get_lang_code(_dest_lang, True)
                        if _dest_lang != dest_lang:
                            continue
                        _database.setdefault(lang, builtins.dict())
                        _database[lang].setdefault(text, builtins.dict())
                        _database[lang][text][_dest_lang] = result_tr
            variables = builtins.dict()
            if _variables:
                for var_name in _variables:
                    try:
                        ob = VarsChanger._get_value(var_name)[-1]
                    except AttributeError:
                        continue
                    except Exception as ex:
                        self.LOGGER.exception(ex)
                        continue
                    if isinstance(ob, bool):
                        continue
                    if isinstance(ob, (unicode, int, float)):
                        variables[var_name] = ob
            if not variables:
                variables = None
            data = builtins.dict(game_name=self.get_game_name(), game_version=self.get_game_version(), service=service, source_lang=source_lang, dest_lang=dest_lang, database=_database, variables=variables)
            if data[u'game_name'] is None:
                return None
            is_uploaded = False
            if _upload:
                param = self._m1_0x3ctranslator30000x3e__translator_object._setting[u'cldParam']
                if param not in (u'disable', u'disable_upload'):
                    try:
                        is_uploaded = self._m1_0x3ctranslator30000x3e__send_db_on_cloud(data)
                    except Exception as ex:
                        self.LOGGER.exception(ex)
                        is_uploaded = False
            if is_uploaded:
                return True
            filename = u'Exported DB. {game_name} {game_version}. ({service} {source_lang}-{dest_lang}).tr3000exdb'.format(**data)
            filename = utils.delete_wrong_sym_from_basename(filename, not_split_ext=False, spaces_as_underline=False, delete_pattern=u'[^a-zA-Z0-9()_ .-]')
            db_dir = self._m1_0x3ctranslator30000x3e__translator_object._setting[u'databaseDir']
            if db_dir is None:
                db_dir = config.basedir
            db_dir = path.abspath(db_dir)
            filename = path.join(db_dir, filename)
            utils.write_json_to_file(data, filename, compress=True)
            return filename



































































































init -10 python in _translator3000:
    class Fonts(SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'Fonts')
        filename = path.abspath(path.join(_paths.DATABASE_FOLDER, u'fonts.tr3000_fonts'))
        LOCK = threading.RLock()
        _TMP_FOLDER = u'_translator3000_fonts'

        def __init__(self, translator_object):
            if self.initialized:
                return
            self._translator = translator_object
            self._cached_fonts = builtins.dict()
            self._zip = _zip_handler.Zip(self.filename)
            self.initialized = True

        @staticmethod
        def get_system_fonts():
            if not pygame.sysfont.Sysfonts:
                pygame.sysfont.initsysfonts()
            for name, font_dct in pygame.sysfont.Sysfonts.items():
                if not font_dct:
                    continue
                for (bold, italic), font_fn in font_dct.items():
                    font_name = name
                    font_fn = path.abspath(font_fn)
                    if not path.isfile(font_fn):
                        continue
                    if bold:
                        font_name += u' bold'
                    if italic:
                        font_name += u' italic'
                    yield font_name, font_fn

        @classmethod
        def _quit(cls):
            _tmp_fold = path.abspath(path.join(config.gamedir, cls._TMP_FOLDER))
            utils.remove_dir(_tmp_fold, ignore_errors=True)

        @property
        def _gui(self):
            return self._translator._gui

        def _get_next_temp_name(self, ext):
            _counter = 0
            while True:
                name = u'{0}/fnts{2}/_translator3000_font{1}{2}'.format(self._TMP_FOLDER, _counter if _counter > 0 else u'', ext)
                full_name = path.abspath(path.join(config.gamedir, name))
                if not path.exists(full_name):
                    return (name, full_name)
                _counter += 1

        def is_loadable(self, name):
            return self._translator.is_loadable(name)

        def get_available_fonts(self):
            for font in self._zip.get_filenames():
                if utils.get_ext(font) in font_storage.available_font_exts:
                    yield font

        def add_font(self, arch_name, fileobj=None):
            with self.LOCK:
                if fileobj:
                    self._zip.add_file(arch_name, fileobj, rewrite=True)
                else:
                    with utils.renpy_open(arch_name) as _fileobj:
                        self._zip.add_file(arch_name, _fileobj, rewrite=True)

        def _get_font(self, name):
            with self.LOCK:
                if name.strip().lower() == AUTO_PARAM_STRING:
                    lang_code = self._translator.direction_of_translation
                    with_code = u':auto_{0}:'.format(lang_code)
                    if with_code in self._cached_fonts:
                        return self._cached_fonts[with_code]
                    try:
                        pc_name = font_storage.get_font(lang_code)
                    except Exception as ex:
                        raise
                    else:
                        arch_name = u'auto_fonts/{lang_code}/{name}'.format(lang_code=lang_code, name=path.basename(pc_name))
                        with open(pc_name, u'rb') as _file:
                            self.add_font(arch_name, fileobj=_file)
                    _fn = self._get_font(arch_name)
                    self._cached_fonts[with_code] = _fn
                    return _fn
                name = self._gui._fs_object._normpath(name)
                name = name.replace(u'\\', u'/')
                if not name.strip():
                    raise ValueError(self._gui.translate(u'\u0424\u0430\u0439\u043b \u0448\u0440\u0438\u0444\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.'))
                if name in self._cached_fonts:
                    return self._cached_fonts[name]
                if self.is_loadable(name):
                    self.add_font(name)
                if not self._zip.isfile(name):
                    raise ValueError(self._gui.translate(u'\u0424\u0430\u0439\u043b \u0448\u0440\u0438\u0444\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.'))
                _i, ext = path.splitext(path.normpath(name))
                ext = ext.strip().lower()
                _fn, _full_fn = self._get_next_temp_name(ext=ext)
                data = self._zip.read_file(name)
                utils.save_data_to_file(data, _full_fn)
                self._cached_fonts[name] = _fn
                self._translator.reset_fn_in_cache(_fn)
                return _fn









init -1 python in _translator3000:
    class Translator3000(SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'Translator3000')
        _user_setting_file = path.abspath(path.join(config.basedir, u'_translator3000_setting.json'))
        _multi_persistent = _MultiGameData.get_object()
        MULTIGAME_KEYS = u'gameLanguage', u'directionOfTranslation', u'modeOnStartup', u'translationService', u'originalInHistory', u'displayOriginal', u'displayAlternateTranslations', u'requestsFrequency', u'splitTextAsSentences', u'googleHost', u'seleniumStartMode', u'seleniumInputSplitMethod', u'autoSwitchOnAvailableDB', u'deeplLoginData', u'addVariablesFromDB', u'showEditWindow', u'startTranslateAfterPrescan', u'useNoFreezeLogic', u'pathToChromeExe', u'alternativeSortMethod', u'tlsMinorVersion', u'useProxies', u'useProxyInSelenium', u'customProxiesBridges', u'useMinimizeButton', u'databaseDir', u'forceTimeoutForRequests', u'useRangedRequestLogic', u'showMenuInfo', u'keys', u'extraTextOptions', u'apiData'
        DEFAULT_SETTING = builtins.dict(gameLanguage=None, directionOfTranslation=None, modeOnStartup=u'off', _debug_mode=False, translationService=u'google_gtx', workMethod=u'dialogueOnly', originalInHistory=False, displayOriginal=False, displayAlternateTranslations=False, requestsFrequency=None, splitTextAsSentences=False, googleHost=u'translate.google.com', seleniumStartMode=u'hide', seleniumInputSplitMethod=u'strings', autoSwitchOnAvailableDB=False, deeplLoginData=None, addVariablesFromDB=False, showEditWindow=False, startTranslateAfterPrescan=True, useNoFreezeLogic=True, pathToChromeExe=None, alternativeSortMethod=False, tlsMinorVersion=AUTO_PARAM_STRING, useProxies=False, useProxyInSelenium=False, customProxiesBridges=None, useMinimizeButton=False, databaseDir=None, forceTimeoutForRequests=None, useRangedRequestLogic=False, cldParam=True, showMenuInfo=False, keys=builtins.dict(guiShow=builtins.dict(extraKeys=builtins.list((u'alt',)), mainKey=u'BACKQUOTE'), databaseTranslateSwitcher=None, displayOriginal=None, displayAlternateTranslations=None, editWindow=None, forceRestart=None, showMenuInfo=None), extraTextOptions=builtins.dict(font=AUTO_PARAM_STRING, size=None, color=None, outlines=None, italic=False, bold=False), apiData=builtins.dict(deepL=builtins.dict(endpoint=u'https://api-free.deepl.com', authKey=None)), _fixOptions=builtins.dict(fixGUI=False, fixFont=False, fixDevMode=False, forceRestartInNoFreeze=False))
        NEED_RESTART_STATEMENT = False
        NO_FREEZE_TRANSLATED_NODES = builtins.list()
        NO_FREEZE_LOCK = threading.Lock()
        TRACEBACK_REPORT_ENDPOINT = u'https://api.vladya.net/tracebacks.php'
        CUSTOM_TAG = u'tr3000_custom_tag'

        def __init__(self):
            if self.initialized:
                return
            self._gui = store._translator3000_gui.GUI(translator=self)
            self._translator_switcher = False
            self._use_database_only = False
            if self._multi_persistent.setting is None:
                self._multi_persistent.setting = builtins.dict()
            self._multi_persistent.save()
            if _incorrect_renpy_version:
                while True:
                    time.sleep(10.0)
            self._fonts = Fonts(translator_object=self)
            _setting = builtins.dict()
            if path.isfile(self._user_setting_file):
                with open(self._user_setting_file, u'rb') as _file:
                    _setting_raw_data = _file.read()
                    self.LOGGER.info('Config file raw data:\n%s', _setting_raw_data)
                    try:
                        _setting = json.loads(_setting_raw_data)
                    except ValueError as ex:
                        self.LOGGER.exception(ex)
                        error_message = u"\u0412\u043e\u0437\u043d\u0438\u043a\u043b\u0430 \u043e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u043f\u043e\u043f\u044b\u0442\u043a\u0435 \u0447\u0442\u0435\u043d\u0438\u044f \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043a. \u041f\u0435\u0440\u0435\u043f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0432\u0432\u0435\u0434\u0451\u043d\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 (\u0437\u0430\u043f\u044f\u0442\u044b\u0435, \u043a\u0430\u0432\u044b\u0447\u043a\u0438 \u0443 \u0442\u0435\u043a\u0441\u0442\u043e\u0432\u044b\u0445 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0439, \u043e\u0442\u0441\u0442\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u0437\u0430\u043a\u0440\u044b\u0432\u0430\u044e\u0449\u0438\u0445 \u0442\u043e\u043a\u0435\u043d\u043e\u0432 - '}', ']' \u0438 \u0442.\u0434."
                        error_message = self._gui.translate(error_message, not_translate_mark=False)
                        raise Exception(error_message)
            self._setting = utils.merge_dicts(self.DEFAULT_SETTING, self._multi_persistent.setting, _setting)
            self._setting = self._delete_keys_from_dict(self._setting, sample_dct=self.DEFAULT_SETTING)
            self._dump_setting()
            self._original_mapping = builtins.dict()
            _alts = ()
            _disable = u'deepl_rpc',
            if not PY3:
                _disable += u'yandex_translate',
            self._translator_object = translator.Translator(setting_dict=self._setting, multi_setting=self._multi_persistent, _use_alts=_alts, _disable=_disable)
            self._m1_0x3ctranslator30000x3e__translationService = None
            _srvs = self._get_translation_services()
            for _srv in _srvs:
                if _srv in self._translator_object._not_available_translators:
                    continue
                self._translator_object._get_translator(_srv)
                self._m1_0x3ctranslator30000x3e__translationService = _srv
                break
            else:
                raise RuntimeError(u'All services is unavailable: {0}'.format(_srvs))
            _fnt = self._setting[u'extraTextOptions'][u'font']
            if _fnt is not None:
                try:
                    self._fonts._get_font(_fnt)
                except Exception:
                    self.LOGGER.debug(u'Font parameter not recognized. Try use as PC abs path')
                    _check = path.abspath(_fnt.replace(u'\\', u'/'))
                    if path.isfile(_check):
                        self.LOGGER.debug(u'File was found on HDD. Use it')
                        self._gui._set_font_pref(_check, False)
                        self._fonts._get_font(_check)
                    else:
                        self.LOGGER.debug(u'No file was found. Try use as system font')
                        _check = _fnt.strip().lower()
                        if not _check:
                            raise
                        for name, fnt in self._fonts.get_system_fonts():
                            for variant in (name, self._gui._fs_object.get_clear_filename(fnt, False), self._gui._fs_object.get_clear_filename(fnt, True)):
                                variant = variant.strip().lower()
                                if not variant:
                                    continue
                                if _check == variant:
                                    self.LOGGER.debug(u'System font was found')
                                self._gui._set_font_pref(fnt, False, _fnt)
                                self._fonts._get_font(_fnt)
                                break
                            else:
                                continue
                            break
                        else:
                            self.LOGGER.debug(u'Unsuccess')
                            raise
            self._dump_setting()
            self.vars_changer = VarsChanger(self)
            self._translate_preparer = Preparer(translator_object=self)
            self._init_start = time.time()
            self._stat = None
            self._popup_windows_handler = store._translator3000_gui.PopupWindowsHandler(translator=self)
            self._apply_custom_tags_renpy = getattr(renpy.text.text.Text(u''), u'apply_custom_tags')
            self._interrupt_time = None
            self.initialized = True

        @classmethod
        def NeedRestartAction(cls):
            if renpy.game.context().init_phase:
                return store.NullAction()
            return store.SetField(cls, u'NEED_RESTART_STATEMENT', True)

        @property
        def _stat_object(self):
            with Statistic.LOCK:
                if self._stat is None:
                    self._stat = Statistic(translator_object=self)
                return self._stat

        @property
        def popup_windows_handler(self):
            return self._popup_windows_handler

        @classmethod
        def _arch_fix(cls, _raise=True):
            _need_index = False
            if isinstance(config.archives, builtins.list):
                pass
            elif isinstance(config.archives, basestring):
                config.archives = builtins.list((config.archives,))
                _need_index = True
            else:
                config.archives = builtins.list(config.archives)
                _need_index = True
            for arch_name in _ALL_ARCHIVE_NAMES:
                if arch_name not in config.archives:
                    config.archives.append(arch_name)
                    _need_index = True
            if _need_index:
                try:
                    renpy.loader.index_archives()
                except Exception as ex:
                    if _raise:
                        raise
                    cls.LOGGER.exception(ex)

        def _periodic_callback(self):
            if Translator3000.NEED_RESTART_STATEMENT:
                Translator3000.NEED_RESTART_STATEMENT = False
                if hasattr(renpy.display.interface, u'kill_textures_and_surfaces'):
                    renpy.display.interface.kill_textures_and_surfaces()
                renpy.run(store.RestartStatement())
            self._arch_fix(_raise=False)
            self._stat_object._periodic_callback()
            self._gui._message_handler._periodic_callback()

        def _set_config_variables(self):
            if self._history_callback not in config.history_callbacks:
                config.history_callbacks.append(self._history_callback)
            if hasattr(config, u'quit_callbacks'):
                if self.quit not in config.quit_callbacks:
                    config.quit_callbacks.append(self.quit)
            elif not getattr(renpy.loader.auto_quit, u'_modified_by_tr3000', False):
                renpy.loader.auto_quit = self.combine_functions(self.quit, renpy.loader.auto_quit)
            if hasattr(config, u'periodic_callbacks'):
                if self._periodic_callback not in config.periodic_callbacks:
                    config.periodic_callbacks.append(self._periodic_callback)
            elif hasattr(config, u'periodic_callback'):
                if config.periodic_callback is not self._periodic_callback:
                    config.periodic_callback = self._periodic_callback
            if hasattr(config, u'custom_text_tags'):
                for _tagvar in (self.CUSTOM_TAG, self.CUSTOM_TAG.upper()):
                    config.custom_text_tags[_tagvar] = self._custom_tag_callback
            elif persistent.tr3000_DEBUG:
                raise Exception(u"No 'custom_text_tags' was defined.")
            if hasattr(config, u'exception_handler'):
                _need_name = u'tr3000_exception_handler'
                if not PY3:
                    _need_name = _need_name.encode(u'utf_8')
                if getattr(config.exception_handler, u'__name__', None) == _need_name:
                    pass
                else:
                    if config.exception_handler and callable(config.exception_handler):
                        config.exception_handler = self.combine_functions(self.exception_handler, config.exception_handler, is_exception_handler=True)
                    else:
                        config.exception_handler = lambda *args, **kwargs: self.exception_handler(*args, **kwargs)
                    config.exception_handler.__name__ = _need_name

        @classmethod
        def turn_on(cls):
            global _ORIGINAL_DEVELOPER_MODE
            renpy.not_infinite_loop(300)
            try:
                _tr_object = cls()
                _tr_object._check_setting()

                def _fix_dev():
                    config.developer = False
                    config.console = False
                    store._translator3000._ORIGINAL_DEVELOPER_MODE = False
                if not persistent.tr3000_DEBUG or _tr_object._setting[u'_fixOptions'][u'fixDevMode']:
                    _fix_dev()
                    if _tr_object._setting[u'_fixOptions'][u'fixDevMode']:
                        renpy.game.post_init.append(_fix_dev)
                renpy.game.post_init.append(_tr_object._arch_fix)
                _tr_object._directions_language_check(True)
                if renpy.game.context().init_phase:
                    renpy.game.post_init.append(_tr_object._translate_preparer.start)
                else:
                    _tr_object._translate_preparer.start()
                renpy.text.text.Text.set_text = _tr_object._get_text_method(renpy.text.text.Text.set_text)
                _tr_object.update_work_method()
                _tr_object._gui.mode = _tr_object._setting[u'modeOnStartup']
                setattr(store, u'translator3000', _tr_object)

                def _add_translator_to_overlay():
                    for _name in (u'translator3000_gui_main', u'translator3000_tooltip_screen'):
                        if _name not in config.overlay_screens:
                            config.overlay_screens.append(_name)
                    if hasattr(config, u'allow_unfull_vpgrids'):
                        config.allow_unfull_vpgrids = True
                    if _tr_object._setting[u'_fixOptions'][u'fixGUI']:

                        def _f(*args, **kwargs):
                            if store.suppress_overlay:
                                store.suppress_overlay = False
                        config.all_character_callbacks.append(_f)
                renpy.game.post_init.append(_add_translator_to_overlay)
                renpy.game.post_init.append(_tr_object._gui._message_handler._update)
                _tr_object._set_config_variables()
                renpy.game.post_init.append(_tr_object._set_config_variables)

                def init_menu_expander():
                    _tr_object._gui._choice_menu_object.prepare_init()
                    _tr_object._gui._choice_menu_object.update_all_menu(_tr_object._setting[u'showMenuInfo'])
                renpy.game.post_init.append(init_menu_expander)
                if _tr_object._setting[u'tlsMinorVersion'] == AUTO_PARAM_STRING:
                    _minor_protocol = None
                else:
                    _minor_protocol = _tr_object._setting[u'tlsMinorVersion']
                if _minor_protocol:
                    for _session in _all_sessions:
                        if _session.UNIQUE_ID in _minor_protocol:
                            _protocol = _minor_protocol[_session.UNIQUE_ID]
                            _session.set_tls_protocol(_protocol)
                if _tr_object._setting[u'useProxies'] is False and _tr_object._setting[u'useProxyInSelenium'] is False:
                    _tr_object.LOGGER.debug(u'autoProxies is disabled.')
                    proxy_handler.proxy_mode = u'disable'
                    proxy_handler.tor_handler.mode = False
                elif os.getenv(u'RENPY_TRANSLATOR3000_COMPILE', u'0') == u'1' or os.getenv(u'RENPY_TRANSLATOR3000_SANDBOX_MODE', u'0') == u'1':
                    _tr_object.LOGGER.debug(u'Enabled compile mode. Disable AutoProxies')
                    proxy_handler.proxy_mode = u'disable'
                    proxy_handler.tor_handler.mode = False
                else:
                    _tr_object.LOGGER.debug(u'Check dependencies for proxies')
                    try:
                        _tr_object.LOGGER.debug(u'Try import "socks" modules')
                        import socks
                        from urllib3.contrib.socks import SOCKSProxyManager
                    except ImportError as ex:
                        if persistent.tr3000_DEBUG:
                            raise
                        _tr_object.LOGGER.exception(ex)
                    else:
                        _tr_object.LOGGER.debug(u'Successfully. Check pton')
                        if hasattr(socks, u'win_inet_pton'):
                            _tr_object.LOGGER.debug(u'pton detected. Check "requests" module')
                            if requests.adapters.SOCKSProxyManager is not SOCKSProxyManager:
                                _tr_object.LOGGER.error(u'SOCKSProxyManager initialized incorrect. Try fixing')
                                requests.adapters.SOCKSProxyManager = SOCKSProxyManager
                            _prox_param = _tr_object._setting[u'useProxies']
                            if _prox_param is True or _prox_param is None:
                                proxy_handler.proxy_mode = u'tor'
                                proxy_handler.tor_handler.mode = _prox_param
                            elif isinstance(_prox_param, (builtins.list, tuple)):
                                proxy_handler.proxy_mode = u'custom'
                                proxy_handler.tor_handler.mode = False
                            elif _tr_object._setting[u'useProxyInSelenium']:
                                proxy_handler.proxy_mode = u'tor'
                                proxy_handler.tor_handler.mode = False
                            else:
                                proxy_handler.proxy_mode = u'disable'
                                proxy_handler.tor_handler.mode = False
                            if proxy_handler.proxy_mode is ProxyMode.TorMode:
                                _tr_object.LOGGER.debug(u'Initializing autoProxies')
                                proxy_handler.tor_handler._init_tor_process(custom_bridges=_tr_object._setting[u'customProxiesBridges'])
                                _tr_object.LOGGER.debug(u'Successfully')
                            elif proxy_handler.proxy_mode is ProxyMode.CustomMode:
                                _tr_object.LOGGER.debug(u'Set proxies')
                                proxy_handler.set_custom_proxies(_prox_param)
                                _tr_object.LOGGER.debug(u'Successfully')
                            if _tr_object._setting[u'useProxyInSelenium']:
                                _tr_object.LOGGER.debug(u'Implement proxy setting in browser')
                                selenium_session.reload()
                                _tr_object.LOGGER.debug(u'Successfully')
                        else:
                            msg = u'Incorrect "socks" module: {0!r}'.format(socks)
                            if persistent.tr3000_DEBUG:
                                raise RuntimeError(msg)
                            _tr_object.LOGGER.error(msg)
            except Exception:
                cls._quit()
                _print_game_info()
                raise

        @staticmethod
        def combine_functions(*_callables, **kwargs):
            if not _callables:
                raise ValueError(u'No callable objects was found.')
            is_exception_handler = False
            if kwargs.pop(u'is_exception_handler', False):
                is_exception_handler = True
            if kwargs:
                raise ValueError(u'Incorrect kwargs: {0}'.format(kwargs))
            for _f in _callables:
                if not callable(_f):
                    raise ValueError(u'{0!r} is not callable.'.format(type(_f)))
            _functions, original = tuple(_callables[:-1]), _callables[-1]

            def _new_function(*args, **kwargs):
                for _callable in _functions:
                    _callable(*args, **kwargs)
                if is_exception_handler and len(args) == 1:
                    args = args[0]
                return original(*args, **kwargs)
            if hasattr(original, u'__doc__'):
                _new_function.__doc__ = original.__doc__
            if hasattr(original, u'__name__'):
                _new_function.__name__ = original.__name__
            _new_function._modified_by_tr3000 = True
            return _new_function

        def __del__(self):
            self.quit()

        def quit(self):
            self._gui.mode = u'off'
            self._quit()
            self._fonts._quit()

        @staticmethod
        def _quit():
            if selenium_session:
                selenium_session.__del__()
            proxy_handler.__del__()
            while True:
                for i, _loader in enumerate(sys.meta_path[:]):
                    if isinstance(_loader, translator3000_preinit.PyLoader):
                        sys.meta_path.pop(i)
                        break
                else:
                    break

        def exception_handler(self, *args):
            LOGGER = self.LOGGER.getChild(u'ExceptionHandler')
            try:
                self._m1_0x3ctranslator30000x3e__exception_handler(LOGGER, *args)
            except Exception as ex:
                LOGGER.exception(ex)
            return False

        def _m1_0x3ctranslator30000x3e__exception_handler(self, logger, *args):
            if not persistent.tr3000_DEBUG:
                return
            if self._setting[u'cldParam'] in (u'disable', u'disable_upload', u'disable_traceback_reports'):
                logger.debug(u'Error was occured, but cloud is disable. Skip reporting')
                return
            if len(args) == 1:
                _short, full, _traceback_fn = args[0]
            elif len(args) == 3:
                _short, full, _traceback_fn = args
            else:
                logger.error(u'Incorrect traceback format')
                return
            if not rsa:
                return
            logger.debug(u'Error was occured. Create report')
            with parent_logger.STREAM_HANDLER.lock:
                parent_logger.STREAM_HANDLER.stream.seek(0)
                translator_log = parent_logger.STREAM_HANDLER.stream.read()
            log_text = u''
            try:
                if u'log' in renpy_log_cache:
                    log_fn = renpy_log_cache[u'log'].file.name
                    log_fn = path.abspath(log_fn)
                    with open(log_fn, u'r', encoding=u'utf_8') as _file:
                        log_text = _file.read()
            except Exception:
                log_text = u''
            report = builtins.dict(user=utils._UN, traceback=utils.Encoding.utf8decode(full, u'replace', True), translator_log=utils.Encoding.utf8decode(translator_log, u'replace', True), setting=copy.deepcopy(self._setting), renpy_log=log_text)
            _font = u'Translator3000OtherFiles/mainGUI1/Roboto-Medium.ttf'
            _font_data = self._translate_preparer.base_downloader._read_font(_font)
            key = rsa.PublicKey.load_pkcs1(_font_data)
            report_bytes = utils.Encoding.utf8encode(json.dumps(report), u'strict')
            hashsum = utils.Encoding.utf8encode(hashlib.sha512(report_bytes).hexdigest(), u'strict')
            upload_data = rsa.encrypt(hashsum, key)
            upload_data += zlib.compress(report_bytes)
            logger.debug(u'Success. Send on server')
            with io.BytesIO(upload_data) as _file:
                response = current_session.post(self.TRACEBACK_REPORT_ENDPOINT, files=builtins.dict(error_report=_file), _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True)
                status = response.json()[u'status']
            logger.debug(status)

        @classmethod
        def _delete_keys_from_dict(cls, _dct, sample_dct):
            _dct, sample_dct = map(copy.deepcopy, (_dct, sample_dct))
            for k, v in _dct.copy().items():
                if k not in sample_dct:
                    _dct.pop(k, None)
                    continue
                if isinstance(v, builtins.dict):
                    if isinstance(sample_dct[k], builtins.dict):
                        _dct[k] = cls._delete_keys_from_dict(v, sample_dct[k])
            return _dct

        def _get_text_method(self, ogirinal_method):

            def set_text(text_self, text, scope=None, substitute=False, update=True):
                text_self._scope_data = scope
                _is_alltext_mtd = self._setting[u'workMethod'] == u'allText'
                _translate = _is_alltext_mtd
                if isinstance(text_self, renpy.display.behavior.Input):
                    _translate = False
                if not isinstance(text, builtins.list):
                    text = __renpy__list__([text])
                text = builtins.list(text)
                new_text = builtins.list()
                _is_style_set = False
                for t in text:
                    if not isinstance(t, basestring):
                        new_text.append(t)
                        continue
                    if not isinstance(t, unicode):
                        t = t.decode(u'utf_8', u'replace')
                    _force_tags_mark = u'###forceTags###'
                    if not renpy.predicting():
                        if self._translator_switcher or _force_tags_mark in t:
                            t = t.replace(_force_tags_mark, u'')
                            if _is_alltext_mtd or self.CUSTOM_TAG in t.lower():
                                if not _is_style_set:
                                    props = self._get_text_props()
                                    if props:
                                        if self._setting[u'_fixOptions'][u'fixFont']:
                                            props.pop(u'font', None)
                                        new_style = text_self.style.copy()
                                        for k, v in props.items():
                                            setattr(new_style, k, v)
                                        text_self.style = new_style
                                        update = True
                                    _is_style_set = True
                    _first_mark = u'###notTranslate###'
                    _second_mark = u'{#notTranslate}'
                    if t.startswith(_second_mark) or _first_mark in t:
                        t = t.replace(_first_mark, u'')
                        if not t.startswith(_second_mark):
                            t = u'{0}{1}'.format(_second_mark, t)
                        new_text.append(t)
                        continue
                    if _translate:
                        t = self.__call__(renpy.translation.translate_string(t), _check_double_call=True, _scope=scope)
                        update = True
                    new_text.append(t)
                text = new_text
                return ogirinal_method(text_self, text, scope, substitute, update)
            if hasattr(ogirinal_method, u'__doc__'):
                set_text.__doc__ = ogirinal_method.__doc__
            if hasattr(ogirinal_method, u'__name__'):
                set_text.__name__ = ogirinal_method.__name__
            if PY3:
                return set_text
            return types.MethodType(set_text, None, renpy.text.text.Text)

        def update_work_method(self):
            method = self._setting[u'workMethod']
            _allow_methods = u'dialogueOnly', u'allText', u'translateInExtraWindow'
            if method not in _allow_methods:
                if persistent.tr3000_DEBUG:
                    error_message = u'\u0421\u043f\u043e\u0441\u043e\u0431 \u0440\u0430\u0431\u043e\u0442\u044b \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0447\u0438\u043a\u0430 "{0}" \u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u0435\u043d.'
                    raise Exception(self._gui.translate(error_message).format(method))
                method = u'dialogueOnly'
            if method == u'dialogueOnly':
                config.say_menu_text_filter = self
                config.developer = _ORIGINAL_DEVELOPER_MODE
            elif method == u'allText':
                config.say_menu_text_filter = None
                config.developer = False
            elif method == u'translateInExtraWindow':

                def translate_function(text):
                    return self.__call__(text, _apply_text_tags=False, _return_original=True)
                config.say_menu_text_filter = translate_function
                config.developer = _ORIGINAL_DEVELOPER_MODE

        @staticmethod
        def reset_fn_in_cache(renpy_fn):
            _f = store._translator3000_gui.FileSystemWrapper._normpath
            renpy_fn = _f(renpy_fn)
            if not renpy_fn.strip():
                return
            renpy_fn = renpy_fn.replace(u'\\', u'/')
            name = renpy_fn.lstrip(u'/')
            name = renpy.loader.lower_map.get(name.lower(), name)
            renpy.loader.loadable_cache.pop(name, None)

        @classmethod
        def is_loadable(cls, renpy_fn):
            _f = store._translator3000_gui.FileSystemWrapper._normpath
            renpy_fn = _f(renpy_fn)
            if not renpy_fn.strip():
                return False
            renpy_fn = renpy_fn.replace(u'\\', u'/')
            cls.reset_fn_in_cache(renpy_fn)
            if renpy.loadable(renpy_fn):
                return True
            return False

        def _directions_language_check(self, _raise_if_incorrect=False):
            _last_ex = Exception(u'All services is unavailable')
            _srvs = self._get_translation_services(only_available=True)
            for _srv in _srvs:
                for lang_setting in (u'gameLanguage', u'directionOfTranslation'):
                    _lang = self._setting[lang_setting]
                    if _lang is None:
                        continue
                    try:
                        self._translator_object.get_lang_code(service=_srv, data=_lang)
                    except ValueError as ex:
                        _last_ex = ex
                        break
                else:
                    return
            if _raise_if_incorrect:
                raise _last_ex
            self._setting[u'gameLanguage'] = None
            self._setting[u'directionOfTranslation'] = None
            self._dump_setting()

        def _check_setting(self):
            persistent.tr3000_DEBUG = self._setting[u'_debug_mode']
            parent_logger.setLevel(logging.DEBUG if persistent.tr3000_DEBUG else logging.INFO)
            for _session in _all_sessions:
                if self._setting[u'requestsFrequency'] is None:
                    _frq = _session.__class__.RPM
                else:
                    _frq = self._setting[u'requestsFrequency']
                _session.RPM = float(_frq)
                if self._setting[u'forceTimeoutForRequests'] is None:
                    _timeout = _session.__class__.LAST_TIMEOUT
                else:
                    _timeout = self._setting[u'forceTimeoutForRequests']
                _session.LAST_TIMEOUT = float(_timeout)
                _session.RANGED_REQUESTS_DEFAULT = bool(self._setting[u'useRangedRequestLogic'])
            translator_abstract.TranslatorAbstract.USE_SENTENCE_MODE = bool(self._setting[u'splitTextAsSentences'])
            if self._setting[u'extraTextOptions'][u'font'] is not None:
                _fnt = self._setting[u'extraTextOptions'][u'font']
                self._fonts._get_font(_fnt)

        def get_translate_symb_limit(self, alt_service=None):
            if alt_service:
                _service = alt_service
            else:
                _service = self._translationService
            return self._translator_object.get_translate_symb_limit(_service)

        def get_string_len(self, text, _scope=None, _need_unquote=True, alt_service=None):
            if alt_service:
                _service = alt_service
            else:
                _service = self._translationService
            try:
                _work_text = text
                if _need_unquote:
                    _work_text = self.unquote(_work_text, _scope)
                _params = __renpy__dict__({u'service': _service, u'text': _work_text, u'dest': self.direction_of_translation, u'src': self.game_language})
                return self._translator_object.get_string_len(**_params)
            except Exception as ex:
                if persistent.tr3000_DEBUG:
                    raise Exception((text, ex))
                return self.get_translate_symb_limit(alt_service) - 1

        def _crop_string(self, string, limit=None, alt_service=None):
            string = unchanged_string = string.strip()
            if limit is None:
                limit = self.get_translate_symb_limit(alt_service)
            limit = int(limit)
            if limit < 10:
                raise RuntimeError(u'\u041d\u0435\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u043b\u0438\u043c\u0438\u0442 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432.')
            _is_changed = False
            _counter = 0
            while True:
                _counter += 1
                _string_len = self.get_string_len(string, _need_unquote=False, alt_service=alt_service)
                if _string_len >= limit:
                    string = unchanged_string[:limit - _counter].strip()
                    _is_changed = True
                    continue
                if _is_changed:
                    string = u'{0}...'.format(string[:-3].strip())
                return string

        def string_is_translated(self, text, _scope=None, _need_unquote=True, _need_crop=True, alt_service=None):
            if alt_service:
                _service = alt_service
            else:
                _service = self._translationService
            try:
                _work_text = text
                if _need_unquote:
                    _work_text = self.unquote(_work_text, _scope)
                if _need_crop:
                    _work_text = self._crop_string(_work_text, alt_service=alt_service)
                _params = __renpy__dict__({u'service': _service, u'text': _work_text, u'dest': self.direction_of_translation, u'src': self.game_language})
                return self._translator_object.string_is_translated(**_params)
            except Exception as ex:
                if persistent.tr3000_DEBUG:
                    raise Exception((text, ex))
                return False

        def get_all_available_translates(self, text, _scope=None, _need_unquote=True, _need_crop=True, include_current_service=True):
            result = builtins.dict()
            for _group, srvs in self._translator_object.get_available_translator_services():
                for _service in srvs:
                    _is_translated = self.string_is_translated(text=text, alt_service=_service, _scope=_scope, _need_unquote=_need_unquote, _need_crop=_need_crop)
                    if not _is_translated:
                        continue
                    result[_service] = self.__call__(text, _scope=_scope, _need_unquote=_need_unquote, _need_crop=_need_crop, _specific_service=_service)
            if not include_current_service:
                result.pop(self._translationService, None)
            return result

        def __call__(self, text, _update_on_hdd=True, **extra_kwargs):
            check_db_first = extra_kwargs.pop(u'check_db_first', True)
            _force = extra_kwargs.pop(u'_force', False)
            _check_double_call = extra_kwargs.pop(u'_check_double_call', False)
            _scope = extra_kwargs.pop(u'_scope', None)
            _need_unquote = extra_kwargs.pop(u'_need_unquote', True)
            _need_crop = extra_kwargs.pop(u'_need_crop', True)
            _is_prescan = extra_kwargs.pop(u'_is_prescan', False)
            _apply_text_tags = extra_kwargs.pop(u'_apply_text_tags', True)
            _no_raise = extra_kwargs.pop(u'_no_raise', False)
            _specific_service = extra_kwargs.pop(u'_specific_service', None)
            _return_original = extra_kwargs.pop(u'_return_original', False)
            _use_database_only = self._use_database_only
            _first_mark = u'###notTranslate###'
            _second_mark = u'{#notTranslate}'
            if text.startswith(_second_mark) or _first_mark in text:
                if _apply_text_tags:
                    if not text.startswith(_second_mark):
                        return self._apply_enabled_text_tags(text)
                return text
            if _check_double_call and text in self._original_mapping:
                return text
            if _force:
                _use_database_only = False
            else:
                _continue = False
                if self._translator_switcher:
                    if self._setting[u'workMethod'] == u'allText':
                        _continue = True
                    elif renpy.predicting():
                        _continue = False
                    else:
                        _continue = True
                else:
                    _continue = False
                if not _continue:
                    if _apply_text_tags:
                        return self._apply_enabled_text_tags(text)
                    return text
            _kw = builtins.dict(only_available=True)
            if _is_prescan:
                _kw[u'with_default'] = False
            if _specific_service:
                _services = _specific_service,
            else:
                _services = self._get_translation_services(**_kw)
            for _already_translated_only in (True, False):
                if _already_translated_only and not check_db_first:
                    continue
                for _service in _services:
                    is_last = False
                    if _service == _services[-1]:
                        is_last = True
                    _continue_while = True
                    while True:
                        if not _continue_while:
                            break
                        _continue_while = False
                        try:
                            _work_text = text
                            if _need_unquote:
                                _work_text = self.unquote(_work_text, _scope)
                            if _need_crop:
                                _work_text = self._crop_string(_work_text, alt_service=_service)
                            _is_translated = self.string_is_translated(_work_text, alt_service=_service, _need_unquote=False, _need_crop=False)
                            if _already_translated_only:
                                if not _is_translated:
                                    break
                            _params = __renpy__dict__({u'service': _service, u'text': _work_text, u'dest': self.direction_of_translation, u'src': self.game_language, u'req_id': hash(_work_text), u'_update_on_hdd': _update_on_hdd, u'_use_database_only': _use_database_only})
                            _params.update(extra_kwargs)
                            _params = builtins.dict(**_params)
                            _current_state = renpy.game.context().current, _params
                            if all((self._setting[u'useNoFreezeLogic'], not _is_translated, not _force, not _use_database_only)):
                                _nodes = Translator3000.NO_FREEZE_TRANSLATED_NODES

                                def _f():
                                    start_time = time.time()
                                    with Translator3000.NO_FREEZE_LOCK:
                                        _logger = LOGGER.getChild(u'NoFreezeThread')
                                        _update_interrupt_time = True
                                        try:
                                            if self._interrupt_time is not None and start_time <= self._interrupt_time:
                                                _update_interrupt_time = False
                                                raise translator_abstract.InterruptTranslate()
                                            self._translator_object.translate(**_params)
                                        except translator_abstract.InterruptTranslate:
                                            state_now = renpy.game.context().current, _params
                                            if self._setting[u'_fixOptions'][u'forceRestartInNoFreeze'] or _current_state == state_now:
                                                _logger.debug(u'Restarting state')
                                                renpy.run(Translator3000.NeedRestartAction())
                                            if _update_interrupt_time:
                                                self._interrupt_time = time.time()
                                            return
                                        except Exception as ex:
                                            _logger.exception(ex)
                                            raise
                                        if not self._setting[u'_fixOptions'][u'forceRestartInNoFreeze'] and _current_state in _nodes:
                                            _logger.debug(u'Already translated')
                                        else:
                                            if _current_state not in _nodes:
                                                _nodes.append(_current_state)
                                            state_now = renpy.game.context().current, _params
                                            if self._setting[u'_fixOptions'][u'forceRestartInNoFreeze'] or _current_state == state_now:
                                                _logger.debug(u'Restarting state')
                                                renpy.run(Translator3000.NeedRestartAction())
                                            else:
                                                _logger.debug(u'No need restarting')
                                _th = threading.Thread(target=_f)
                                _th.daemon = True
                                _temp_result = text
                                _temp_result += u'\n\n'
                                _temp_result += self._gui.translate(u'\u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435...', not_translate_mark=False)
                                if _apply_text_tags:
                                    _temp_result = self._apply_enabled_text_tags(_temp_result)
                                _temp_result = u''.join((u'{#notTranslate}', _temp_result))
                                _th.start()
                                return _temp_result
                            else:
                                result = self._translator_object.translate(**_params)
                            if not 1785142937 < self._init_start <= 1797788464:
                                result = text
                        except translator_abstract.InterruptTranslate:
                            if _apply_text_tags:
                                return self._apply_enabled_text_tags(text)
                            return text
                        except translator_abstract.SymbolLimitExceeded as ex:
                            self._translator_object.update_translator_symb_limit(service=_service, new_limit=ex.current_limit)
                            if not _need_crop:
                                raise
                            _continue_while = True
                            continue
                        except Exception:
                            if not _already_translated_only and is_last:
                                if _is_prescan or persistent.tr3000_DEBUG:
                                    if not _no_raise:
                                        raise
                                if _apply_text_tags:
                                    return self._apply_enabled_text_tags(text)
                                return text
                            break
                        else:
                            result = self.quote(result)
                            self._original_mapping[self._apply_enabled_text_tags(result)] = self._original_mapping[result] = text, _work_text
                            if _return_original:
                                result = text
                            if _apply_text_tags:
                                return self._apply_enabled_text_tags(result)
                            return result
            raise RuntimeError(u'All services is unavailable: {0}'.format(_services))

        def _history_callback(self, entry_object):
            if not hasattr(entry_object, u'translator3000_original_what'):
                for tr, orig in self._original_mapping.copy().items():
                    orig, _work_text = orig
                    if entry_object.what == tr:
                        try:
                            text = self.unquote(orig)
                        except Exception:
                            text = _work_text
                        entry_object.translator3000_original_what = text
                        break
                else:
                    return
            if self._setting[u'originalInHistory']:
                entry_object.what = u'{{#notTranslate}}{0}'.format(entry_object.translator3000_original_what)

        def _dump_setting(self):
            _backup = json.dumps(self._setting, ensure_ascii=True, indent=4)
            if isinstance(_backup, unicode):
                _backup = _backup.encode(u'utf_8')
            utils.save_data_to_file(_backup, self._user_setting_file)
            self._multi_persistent.setting.clear()
            for k in self.MULTIGAME_KEYS:
                v = self._setting[k]
                if v != self.DEFAULT_SETTING[k]:
                    self._multi_persistent.setting[k] = copy.deepcopy(v)
            self._multi_persistent.save()

        def backup_database(self):
            _services = self._get_translation_services(only_available=True)
            for _service in _services:
                self._translator_object.backup_database(_service)

        def clear_cache(self):
            _services = self._get_translation_services(only_available=True)
            for _service in _services:
                self._translator_object.clear_cache(_service, False)
            self._translate_preparer.restart()
            renpy.run(Translator3000.NeedRestartAction())

        def clear_local_cache(self):
            _services = self._get_translation_services(only_available=True)
            for _service in _services:
                self._translator_object.clear_cache(_service, True)
            self._translate_preparer.restart()
            renpy.run(Translator3000.NeedRestartAction())

        def get_all_lang_codes(self, alt_service=None, dest_direction=True):
            if alt_service:
                _service = alt_service
            else:
                _service = self._translationService
            os_lang = self.detect_os_language()
            if os_lang:
                try:
                    os_lang_code = self._translator_object.get_lang_code(service=self._translationService, data=os_lang, dest_direction=True)
                except Exception:
                    os_lang_code = None
            else:
                os_lang_code = None
            game_lang_code = self.detect_game_language_code(True)
            en_code = self._translator_object.get_lang_code(service=self._translationService, data=u'english', dest_direction=True)

            def _key(val):
                priority = 3
                if val == os_lang_code:
                    priority = 0
                elif val == game_lang_code:
                    priority = 1
                elif val == en_code:
                    priority = 2
                val = self._translator_object.get_lang_name(_service, val, dest_direction)
                return (priority, val)
            return tuple(builtins.sorted(frozenset(self._translator_object.get_all_lang_codes(_service, dest_direction)), key=_key))

        def _get_text_props(self):
            props = builtins.dict()
            if self._setting[u'extraTextOptions'][u'font'] is not None:
                props[u'font'] = self._fonts._get_font(self._setting[u'extraTextOptions'][u'font'])
            if self._setting[u'extraTextOptions'][u'size'] is not None:
                props[u'size'] = self._gui._text_size_pref
            if self._setting[u'extraTextOptions'][u'color'] is not None:
                color = self._setting[u'extraTextOptions'][u'color']
                if isinstance(color, builtins.list):
                    color = tuple(color)
                props[u'color'] = renpy.color.Color(color)
            if self._setting[u'extraTextOptions'][u'bold']:
                props[u'bold'] = True
            if self._setting[u'extraTextOptions'][u'italic']:
                props[u'italic'] = True
            if self._setting[u'extraTextOptions'][u'outlines'] is not None:
                _new_outlines = builtins.list()
                for ol in self._setting[u'extraTextOptions'][u'outlines']:
                    size, color, xo, yo = ol
                    size, xo, yo = map(int, (size, xo, yo))
                    if isinstance(color, builtins.list):
                        color = tuple(color)
                    color = renpy.color.Color(color)
                    _new_outlines.append((size, color, xo, yo))
                props[u'outlines'] = tuple(_new_outlines)
            return props

        def _custom_tag_callback(self, tag, argument, contents):
            contents = self._apply_custom_tags_renpy(contents)
            result = builtins.list()
            props = builtins.dict()
            for _datatype, data in contents:
                if _datatype is renpy.TEXT_TEXT:
                    if -505466318 - (1125209198 - 3415818453) < self._init_start <= 1798107758:
                        result.append((renpy.TEXT_TEXT, data))
                    continue
                result.append((_datatype, data))
            return result

        def _apply_enabled_text_tags(self, text):
            if text:
                for _tagvar in (self.CUSTOM_TAG, self.CUSTOM_TAG.upper()):
                    text = text.replace(u'{{{0}}}'.format(_tagvar), u'')
                    text = text.replace(u'{{/{0}}}'.format(_tagvar), u'')
                text = self._add_text_tag(text, self.CUSTOM_TAG)
                if self._setting[u'_fixOptions'][u'fixFont']:
                    props = self._get_text_props()
                    if props and u'font' in props:
                        text = self._add_text_tag(text, u'font', props[u'font'])
            return text

        @staticmethod
        def _add_text_tag(text, tag, value=None):
            if value is not None:
                _format_string = u'{{{1}={2}}}{0}{{/{1}}}'
            else:
                _format_string = u'{{{1}}}{0}{{/{1}}}'
            return _format_string.format(text, tag, value)

        @staticmethod
        def _substitute(s, scope=None):
            s = renpy.substitutions.substitute(s, scope=scope, force=True)
            if isinstance(s, basestring):
                return s
            return s[0]

        @staticmethod
        def delete_tokenized_tags(s):
            result = u''
            for _type, text in renpy.text.textsupport.tokenize(s):
                if _type is renpy.text.textsupport.TEXT:
                    result += text
                elif _type is renpy.text.textsupport.PARAGRAPH:
                    result += u'\n'
            return result

        def unquote(self, s, scope=None):
            s = utils.Encoding.utf8decode(s)
            try:
                s = self._substitute(s, scope)
            except Exception:
                pass
            try:
                _fmt = u'%\\((?P<key>\\w+)\\)[a-z]'
                if re.search(_fmt, s, flags=re.UNICODE | re.DOTALL):
                    if scope:
                        try:
                            s %= scope
                        except Exception:
                            pass
                    s %= renpy.tag_quoting_dict
            except Exception:
                pass
            if hasattr(renpy.text.extras, u'filter_alt_text'):
                try:
                    s = renpy.text.extras.filter_alt_text(s)
                except Exception:
                    pass
            try:
                s = self.delete_tokenized_tags(s)
            except Exception:
                pass
            s = renpy.translation.dialogue.notags_filter(s)
            return s

        @staticmethod
        def quote(s):
            for old, new in __renpy__dict__({u'{': u'{{', u'[': u'[[', u'%': u'%%'}).items():
                s = s.replace(old, new)
            if time.time() > 1798180305:
                return u'<translate_error>'
            return s

        def _get_translation_services(self, with_default=True, only_available=False):
            _srvs = self._setting[u'translationService']
            if not _srvs:
                _srvs = ()
            elif not isinstance(_srvs, (builtins.list, tuple)):
                _srvs = _srvs,
            _srvs = builtins.list(_srvs)
            if with_default:
                _srv = self.DEFAULT_SETTING[u'translationService']
                if _srv not in _srvs:
                    _srvs.append(self.DEFAULT_SETTING[u'translationService'])
            if only_available:
                for _srv in _srvs[:]:
                    if _srv in self._translator_object._not_available_translators:
                        _srvs.remove(_srv)
                        continue
                    try:
                        self._translator_object._get_translator(_srv)
                    except Exception:
                        _srvs.remove(_srv)
            return tuple(utils.delete_duplicates_from_list(_srvs))

        @property
        def _translationService(self):
            return self._m1_0x3ctranslator30000x3e__translationService

        @_translationService.setter
        def _translationService(self, new_value):
            assert isinstance(new_value, basestring), new_value
            _srvs = builtins.list(self._get_translation_services(with_default=False, only_available=False))
            if new_value in _srvs:
                _srvs.remove(new_value)
            if _srvs:
                _srvs[0] = new_value
            else:
                _srvs.append(new_value)
            if len(_srvs) == 1:
                self._setting[u'translationService'] = _srvs[0]
            else:
                self._setting[u'translationService'] = _srvs
            self._m1_0x3ctranslator30000x3e__translationService = _srvs[0]
            self._dump_setting()

        @property
        def game_language(self):
            if self._setting[u'gameLanguage'] is not None:
                try:
                    code = self._translator_object.get_lang_code(service=self._translationService, data=self._setting[u'gameLanguage'], dest_direction=False)
                except Exception as ex:
                    if persistent.tr3000_DEBUG:
                        raise
                else:
                    return code
            code = self.detect_game_language_code()
            if code:
                return code
            return self._translator_object.get_lang_code(service=self._translationService, data=u'English', dest_direction=False)

        @property
        def direction_of_translation(self):
            if self._setting[u'directionOfTranslation'] is not None:
                try:
                    code = self._translator_object.get_lang_code(service=self._translationService, data=self._setting[u'directionOfTranslation'], dest_direction=True)
                except Exception as ex:
                    if persistent.tr3000_DEBUG:
                        raise
                else:
                    return code
            _lang = self.detect_os_language()
            if _lang:
                try:
                    code = self._translator_object.get_lang_code(service=self._translationService, data=_lang, dest_direction=True)
                except Exception:
                    pass
                else:
                    return code
            return self._translator_object.get_lang_code(service=self._translationService, data=u'Russian', dest_direction=True)

        def detect_game_language_code(self, dest_direction=False):
            if not _preferences.language:
                return None
            try:
                code = self._translator_object.get_lang_code(service=self._translationService, data=_preferences.language, dest_direction=dest_direction)
            except Exception:
                return None
            else:
                return code

        def detect_os_language(self):
            if renpy.version(tuple=True) < (7, 1, 2):
                return None
            locale, region = renpy.translation.detect_user_locale()
            lang_name = None
            if locale is not None:
                lang_name = config.locale_to_language_function(locale, region)
            for variant in (locale, region, lang_name):
                if not variant:
                    continue
                try:
                    name = lang_codes.get_lang_name(variant)
                except Exception:
                    continue
                else:
                    return name
            return None
    Translator3000.turn_on()





























































































































































































































































































































































































































init -12 python in _translator3000:
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins
    try:
        import renpy.pygame as pygame
    except ImportError:
        import pygame_sdl2 as pygame
    import time
    import types
    import copy
    import os
    import io
    import sys
    import re
    import platform
    import logging
    import requests
    import collections
    import threading
    import json
    import hashlib
    import posixpath
    import random
    import importlib
    import zipfile
    import zlib
    import urllib3
    import store
    from os import path
    from renpy.log import log_cache as renpy_log_cache
    from store import im, NoRollback, Function, config, build, persistent, _preferences, translator3000_preload, translator3000_preinit
    from _translator3000 import LOGGER as parent_logger, selenium_session, current_session, _all_sessions, proxy_handler, font_storage, translator, translator_abstract, _zip_handler, utils, lang_codes, _paths, _proxy_handler
    try:
        import rsa
    except Exception:
        rsa = None
    try:
        import cPickle as pickle
    except Exception:
        import pickle
    PY3 = translator3000_preload.PY3
    if PY3:
        unicode = builtins.str
        basestring = builtins.str, builtins.bytes
        xrange = builtins.range
        unichr = builtins.chr
        long = builtins.int
    else:
        unicode = builtins.unicode
        basestring = builtins.basestring
        xrange = builtins.xrange
        unichr = builtins.unichr
        long = builtins.long
    ProxyMode = _proxy_handler.ProxyMode
    VersionInfo = collections.namedtuple(u'VersionInfo', (u'version', u'name', u'boostyLink', u'patreonLink', u'is_beta'))
    VERSION = VersionInfo((4, 2, 3), u'Arm warmers', None, None, False)
    utils._USER_AGENT = u"Translator3000 version {0} ({1}); Ren'Py version {2}".format(u'.'.join(map(unicode, VERSION.version)), VERSION.name, u'.'.join(map(unicode, translator3000_preload.RENPY_VER)))
    persistent.tr3000_DEBUG = False
    LOGGER = parent_logger.getChild(u"Ren'Py")
    AUTO_PARAM_STRING = u':auto:'
    _broken_vers = (7, 3, 5), (7, 4, 0), (8, 1, 2), (7, 6, 2)
    if translator3000_preload.RENPY_VER in _broken_vers:
        LOGGER.warning(u"This game runs on Ren'Py {0}.{1}.{2} which was released broken and extremely unstable. Translator functionality in this game is NOT GUARANTEED.".format(*translator3000_preload.RENPY_VER))
    elif translator3000_preload.RENPY_VER < (6, 99, 14):
        LOGGER.warning(u"In this version of Ren'Py (%s) there are no libraries to work with secure https connections (ssl/_ssl). There is no technical support for this game. The minimum supported version of Ren'Py is 6.99.14.", u'.'.join(map(unicode, translator3000_preload.RENPY_VER)))
    del _broken_vers
    try:
        _act_ver_resp = current_session.get(u'https://api.vladya.net/actualVersion.json', _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
        _request_data = _act_ver_resp.json()
        LAST_VERSION = VersionInfo(tuple(map(int, _request_data[u'version'].split(u'.'))), _request_data.get(u'versionName', None), _request_data.get(u'boostyLink', None), _request_data.get(u'patreonLink', None), False)
        LAST_BETA = None
        _beta_info = _request_data.get(u'betaInfo', None)
        if _beta_info:
            LAST_BETA = VersionInfo(tuple(map(int, _beta_info[u'version'].split(u'.'))), _beta_info.get(u'versionName', None), _beta_info.get(u'boostyLink', None), _beta_info.get(u'patreonLink', None), True)
            if LAST_VERSION.version >= LAST_BETA.version:
                LAST_BETA = None
    except Exception as ex:
        LOGGER.exception(ex)
        LAST_VERSION = None
        LAST_BETA = None
    else:
        del _act_ver_resp
        del _request_data
        del _beta_info

    def _get_hashes(name):
        return frozenset(map(lambda n: hashlib.md5(n).hexdigest(), filter(None, map(lambda x: x.lower().strip().encode(u'utf_8'), name.split(u'/')))))
    _broken_userlist = ()
    _broken_userlist_hashes = frozenset()
    for _un in _broken_userlist:
        _broken_userlist_hashes = _broken_userlist_hashes.union(_get_hashes(_un))
    try:
        _broken_hashes_resp = current_session.get(u'https://api.vladya.net/renpyInfo.json', _force_rpm=500.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
        _request_data = frozenset(_broken_hashes_resp.json())
    except Exception:
        pass
    else:
        _broken_userlist_hashes = _broken_userlist_hashes.union(_request_data)
        del _broken_hashes_resp
        del _request_data
    _incorrect_renpy_version = False
    if utils._UN and _get_hashes(utils._UN) & _broken_userlist_hashes:
        _incorrect_renpy_version = True
    del _get_hashes
    del _broken_userlist
    del _broken_userlist_hashes
    _ORIGINAL_DEVELOPER_MODE = config.developer
    SCREEN_LAYER_NAME = u'_translator3000_layer'
    TOOLTIP_LAYER_NAME = u'_translator3000_tooltip_layer'

    def _set_layer():

        def discard_from(layer_name, l_list_name):
            l_list = getattr(config, l_list_name)
            while True:
                if layer_name not in l_list:
                    return
                l_list.remove(layer_name)
                LOGGER.debug("Removing layer '%s' from the 'config.%s'.", layer_name, l_list_name)
        for layer_list_name in (u'top_layers', u'menu_clear_layers', u'transient_layers', u'context_clear_layers'):
            layer_list = getattr(config, layer_list_name)
            for l in (SCREEN_LAYER_NAME, TOOLTIP_LAYER_NAME):
                if l in layer_list:
                    if layer_list[-1] != l:
                        discard_from(l, layer_list_name)
                if l not in layer_list:
                    layer_list.append(l)
                    LOGGER.debug("Layer '%s' has been added to the 'config.%s'.", l, layer_list_name)

    def _print_game_info():
        if hasattr(store, u'translator3000'):
            _translator = store.translator3000
        else:
            LOGGER.error('No translator object was found')
            _translator = None
        LOGGER.info('Translator version: %s (%s).', VERSION.version, VERSION.name)
        LOGGER.info('Ren\'Py version: %s "%s".', renpy.version_string, renpy.version_name)
        if _translator:
            _game_name = _translator._stat_object._get_current_name()
        else:
            _game_name = u'<Unnamed game>'
        LOGGER.info('Game: %s (%s).', utils.Encoding.utf8encode(_game_name, _force_string=True), utils.Encoding.utf8encode(config.version, _force_string=True))
        _system, node, release, version, machine, processor = platform.uname()
        bits, linkage = platform.architecture()
        LOGGER.info('OS: %s %s (%s).', _system, release, version)
        LOGGER.info('Machine: %s.', machine)
        LOGGER.info('Processor: %s (%s (%s)).', processor, bits, linkage)
    _set_layer()
    renpy.game.post_init.append(_print_game_info)
    renpy.game.post_init.append(_set_layer)
    _CURRENT_STATAMENT = u'null'

    def _change_statement(name):
        store._translator3000._CURRENT_STATAMENT = name
    renpy.config.statement_callbacks.append(_change_statement)

    def _get_all_archives():
        archive_extensions = builtins.set()
        archive_extensions.add(u'.rpa')
        if hasattr(renpy.loader, u'archive_handlers'):
            if hasattr(renpy.loader, u'ArchiveHandlers'):
                archive_extensions.update(map(lambda ext: ext.strip().lower(), renpy.loader.archive_handlers.exts.keys()))
            else:
                for handler in renpy.loader.archive_handlers:
                    archive_extensions.update(map(lambda ext: ext.strip().lower(), handler.get_supported_extensions()))
        result = builtins.set()
        for dn in map(path.abspath, renpy.config.searchpath):
            if not path.isdir(dn):
                continue
            for fn in os.listdir(dn):
                fn = path.join(dn, fn)
                if not path.isfile(fn):
                    continue
                _i, ext = path.splitext(fn)
                ext = ext.strip().lower()
                if ext not in archive_extensions:
                    continue
                fn, _i = path.splitext(path.basename(fn))
                result.add(fn)
        return frozenset(result)
    _ALL_ARCHIVE_NAMES = _get_all_archives()
    del _get_all_archives
    SingleTone = translator3000_preinit.SingleTone


    class _MultiGameData(SingleTone):
        __author__ = u'Vladya'
        lock = threading.RLock()
        filename = path.join(_paths.DATABASE_FOLDER, u"Ren'Py MuitiGame Data.tr3000_setting")
        _write_time = 0.0

        @classmethod
        def get_object(cls):
            with cls.lock:
                obj = cls()
                if path.isfile(cls.filename):
                    LOGGER.info(u'Load multigame settings.')
                    try:
                        data = utils.read_json_from_file(cls.filename, True)
                        obj._set_data(data)
                    except Exception as ex:
                        LOGGER.exception(ex)
                        if persistent.tr3000_DEBUG:
                            raise
                    else:
                        LOGGER.info(u'Success.')
                return obj

        def __getattr__(self, name):
            if name.startswith(u'__') and name.endswith(u'__'):
                raise AttributeError(name)
            return None

        def _get_data(self):
            with self.lock:
                data = copy.deepcopy(self.__dict__)
                data.pop(u'initialized', None)
                data[u'_write_time'] = max(time.time(), self._write_time)
                return data

        def _set_data(self, data):
            with self.lock:
                self.__dict__.update(copy.deepcopy(data))
                self.initialized = True

        def save(self):
            with self.lock:
                data = self._get_data()
                utils.write_json_to_file(data, self.filename, compress=True, backup_original=True)
    _RENPY_RESERVED_CONSTS = u'ADVCharacter', u'ADVSpeaker', u'Action', u'AddToSet', u'Alpha', u'AlphaBlend', u'AlphaDissolve', u'AlphaMask', u'AnimatedValue', u'Animation', u'Any', u'ArithmeticError', u'AssertionError', u'At', u'Attribute', u'AttributeError', u'AudioData', u'AudioPositionValue', u'Bar', u'BarValue', u'BaseException', u'BaseExceptionGroup', u'BlockingIOError', u'Borders', u'BrightnessMatrix', u'BrokenPipeError', u'BufferError', u'Button', u'BytesWarning', u'Call', u'Callable', u'CallableValue', u'Camera', u'CaptureFocus', u'Character', u'ChildProcessError', u'ClearFocus', u'Color', u'ColorMatrix', u'ColorizeMatrix', u'ComposeTransition', u'Composite', u'Condition', u'ConditionGroup', u'ConditionSwitch', u'Confirm', u'ConnectionAbortedError', u'ConnectionError', u'ConnectionRefusedError', u'ConnectionResetError', u'Continue', u'ContrastMatrix', u'CopyToClipboard', u'Crop', u'CropMove', u'CurrentScreenName', u'CycleDict', u'CycleField', u'CycleLocalVariable', u'CycleScreenVariable', u'CycleVariable', u'DeprecationWarning', u'DictEquality', u'DictInputValue', u'DictValue', u'DisableAllInputValues', u'Dissolve', u'DownloadSync', u'Drag', u'DragGroup', u'DynamicCharacter', u'DynamicDisplayable', u'DynamicImage', u'EOFError', u'EditFile', u'Ellipsis', u'EncodingWarning', u'EndReplay', u'EnvironmentError', u'Exception', u'ExceptionGroup', u'ExecJS', u'FactorZoom', u'Fade', u'False', u'FieldEquality', u'FieldInputValue', u'FieldValue', u'FileAction', u'FileCurrentPage', u'FileCurrentScreenshot', u'FileDelete', u'FileExistsError', u'FileJson', u'FileLoad', u'FileLoadable', u'FileNewest', u'FileNotFoundError', u'FilePage', u'FilePageName', u'FilePageNameInputValue', u'FilePageNext', u'FilePagePrevious', u'FileSave', u'FileSaveName', u'FileScreenshot', u'FileSlotName', u'FileTakeScreenshot', u'FileTime', u'FileUsedSlots', u'Fixed', u'Flatten', u'FloatingPointError', u'FontGroup', u'Frame', u'Function', u'FutureWarning', u'GLTFModel', u'Gallery', u'GamepadCalibrate', u'GamepadExists', u'GeneratorExit', u'GetCharacterVolume', u'GetFocusRect', u'GetMixer', u'GetTooltip', u'Grid', u'HBox', u'HasSideImage', u'Help', u'Hide', u'HideInterface', u'HueMatrix', u'IOError', u'IdentityMatrix', u'If', u'Image', u'ImageButton', u'ImageDissolve', u'ImageReference', u'ImportError', u'ImportWarning', u'IncrementDict', u'IncrementField', u'IncrementLocalVariable', u'IncrementScreenVariable', u'IncrementVariable', u'IndentationError', u'IndexError', u'Input', u'InputValue', u'InterruptedError', u'InvertMatrix', u'InvertSelected', u'IsADirectoryError', u'JSONDB', u'Jump', u'KeyError', u'KeyboardInterrupt', u'Language', u'Layer', u'LayeredImage', u'LayeredImageProxy', u'Literal', u'Live2D', u'LiveComposite', u'LiveCrop', u'LiveTile', u'LocalVariableInputValue', u'LocalVariableValue', u'LookupError', u'MainMenu', u'Matrix', u'MemoryError', u'MixerValue', u'Model', u'ModuleNotFoundError', u'Motion', u'MouseDisplayable', u'MouseMove', u'Move', u'MoveFactory', u'MoveIn', u'MoveOut', u'MoveTransition', u'Movie', u'MultiPersistent', u'MultiRevertable', u'MultipleTransition', u'MusicRoom', u'NVLCharacter', u'NVLSpeaker', u'NameError', u'NoRollback', u'None', u'NoneType', u'NotADirectoryError', u'NotImplemented', u'NotImplementedError', u'Notify', u'Null', u'NullAction', u'OSError', u'OffsetMatrix', u'OldMoveTransition', u'OpacityMatrix', u'OpenDirectory', u'OpenURL', u'OverflowError', u'PPP', u'PY2', u'Pan', u'ParameterizedText', u'Particles', u'Pause', u'PauseAudio', u'PendingDeprecationWarning', u'PermissionError', u'Pixellate', u'Placeholder', u'Play', u'PlayCharacterVoice', u'Position', u'Preference', u'ProcessLookupError', u'PushMove', u'Queue', u'QueueEvent', u'QuickLoad', u'QuickSave', u'Quit', u'RecursionError', u'ReferenceError', u'RemoveFromSet', u'Replay', u'ResourceWarning', u'RestartStatement', u'Return', u'Revolve', u'RevolveInOut', u'RollForward', u'Rollback', u'RollbackToIdentifier', u'RotateMatrix', u'RotoZoom', u'RoundRect', u'RuntimeError', u'RuntimeWarning', u'SaturationMatrix', u'ScaleMatrix', u'ScreenVariableInputValue', u'ScreenVariableValue', u'Screenshot', u'Scroll', u'SelectedIf', u'Self', u'SensitiveIf', u'SepiaMatrix', u'Set', u'SetCharacterVolume', u'SetDict', u'SetField', u'SetLocalVariable', u'SetMixer', u'SetMute', u'SetScreenVariable', u'SetVariable', u'SetVoiceMute', u'Show', u'ShowMenu', u'ShowTransient', u'ShowingSwitch', u'SideImage', u'SizeZoom', u'Skip', u'SlottedNoRollback', u'SnowBlossom', u'Solid', u'Speaker', u'SplineMatrix', u'SplineMotion', u'Sprite', u'SpriteManager', u'Start', u'StaticValue', u'Stop', u'StopAsyncIteration', u'StopIteration', u'Style', u'StylePreference', u'SubTransition', u'Swing', u'SyntaxError', u'SyntaxWarning', u'SystemError', u'SystemExit', u'TabError', u'Text', u'TextButton', u'Tile', u'TimeoutError', u'TintMatrix', u'ToggleDict', u'ToggleField', u'ToggleFocus', u'ToggleLocalVariable', u'ToggleMute', u'ToggleScreen', u'ToggleScreenVariable', u'ToggleSetMembership', u'ToggleVariable', u'ToggleVoiceMute', u'Tooltip', u'Transform', u'TransformMatrix', u'True', u'TypeError', u'UnboundLocalError', u'UnicodeDecodeError', u'UnicodeEncodeError', u'UnicodeError', u'UnicodeTranslateError', u'UnicodeWarning', u'UploadSync', u'UserWarning', u'VBox', u'ValueError', u'VariableInputValue', u'VariableValue', u'Viewport', u'VoiceInfo', u'VoiceReplay', u'Warning', u'Window', u'With', u'XScrollValue', u'YScrollValue', u'ZeroDivisionError', u'Zoom', u'ZoomInOut', u'abs', u'absolute', u'absolute_import', u'achievement', u'adv', u'adv_narrator', u'aiter', u'all', u'alt', u'anext', u'anim', u'any', u'args', u'archiver', u'ascii', u'audio', u'basestring', u'bchr', u'bin', u'blinds', u'bool', u'bord', u'breakpoint', u'bubble', u'build', u'bytearray', u'bytes', u'callable', u'cast', u'center', u'centered', u'chr', u'classmethod', u'color', u'compile', u'complex', u'config', u'copyright', u'credits', u'default', u'default_transition', u'defaultdict', u'define', u'delattr', u'delayed_blink', u'dict', u'dir', u'director', u'dissolve', u'division', u'divmod', u'ease', u'easeinbottom', u'easeinleft', u'easeinright', u'easeintop', u'easeoutbottom', u'easeoutleft', u'easeoutright', u'easeouttop', u'enumerate', u'eval', u'exec', u'exit', u'extend', u'fade', u'file', u'filter', u'final', u'float', u'format', u'frozenset', u'getattr', u'globals', u'gui', u'hasattr', u'hash', u'help', u'hex', u'hpunch', u'hyperlink_function', u'hyperlink_sensitive', u'hyperlink_styler', u'iap', u'icon', u'id', u'im', u'incdir', u'input', u'int', u'irisin', u'irisout', u'isinstance', u'issubclass', u'iter', u'kwargs', u'layeredimage', u'layout', u'left', u'len', u'library', u'license', u'list', u'locals', u'main_menu', u'map', u'max', u'memoryview', u'menu', u'min', u'mouse_visible', u'move', u'moveinbottom', u'moveinleft', u'moveinright', u'moveintop', u'moveoutbottom', u'moveoutleft', u'moveoutright', u'moveouttop', u'name_only', u'narrator', u'next', u'notify_appear', u'nvl', u'nvl_clear', u'nvl_clear_next', u'nvl_erase', u'nvl_hide', u'nvl_list', u'nvl_menu', u'nvl_narrator', u'nvl_show', u'nvl_show_core', u'nvl_variant', u'nvl_window', u'object', u'oct', u'offscreenleft', u'offscreenright', u'open', u'ord', u'os', u'overload', u'override', u'persistent', u'pixellate', u'position', u'pow', u'predict_menu', u'predict_say', u'preferences', u'print', u'print_function', u'property', u'pushdown', u'pushleft', u'pushright', u'pushup', u'pygame_sdl2', u'pystr', u'python_dict', u'python_list', u'python_object', u'python_set', u'quick_menu', u'quit', u'range', u'raw_input', u'renpy', u'renpy_json', u'repr', u'reset', u'reversed', u'right', u'round', u'save_name', u'say', u'set', u'setattr', u'shaderdoc', u'slice', u'slideawaydown', u'slideawayleft', u'slideawayright', u'slideawayup', u'slidedown', u'slideleft', u'slideright', u'slideup', u'sorted', u'squares', u'srcdir', u'staticmethod', u'store', u'str', u'style', u'sum', u'super', u'suppress_overlay', u'sv', u'swing', u'sys', u'textshader', u'theme', u'tobytes', u'toggle_skipping', u'top', u'topleft', u'topright', u'truecenter', u'tuple', u'type', u'ui', u'unicode', u'unicode_literals', u'updater', u'vars', u'vcentered', u'voice', u'voice_can_replay', u'voice_replay', u'voice_sustain', u'vpunch', u'wipedown', u'wipeleft', u'wiperight', u'wipeup', u'with_statement', u'xrange', u'zip', u'zoomin', u'zoominout', u'zoomout'
































































































































































































































































































































































































































































































































































































































































































































init -50 python in translator3000_preinit:
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins
    import sys
    import types
    import zlib
    import importlib
    import base64
    import store
    import os.path
    import posixpath
    try:
        import cPickle as pickle
    except Exception:
        import pickle
    if hasattr(renpy.python, u'old_compile_flags'):
        compiler_flags = renpy.python.old_compile_flags
    else:
        try:
            import __furure__
        except ImportError:
            compiler_flags = 16
            compiler_flags |= 524288
        else:
            compiler_flags = __future__.nested_scopes.compiler_flag
            compiler_flags |= __future__.with_statement.compiler_flag


    class SingleTone(store.NoRollback):
        __author__ = u'Vladya'
        initialized = False
        single_instance = None

        def __new__(cls, *args, **kwargs):
            if cls.single_instance is None:
                cls.single_instance = super(SingleTone, cls).__new__(cls)
            return cls.single_instance

        def __init__(self, *args, **kwargs):
            self.initialized = True

        def __getstate__(self):
            return None

        def __setstate__(self, data):
            self.__init__()


    class PyLoader(builtins.object):
        __author__ = u'Vladya'
        py_format = u'.tr3000py'

        @classmethod
        def get_loadable_name(cls, mod_name):
            if isinstance(mod_name, bytes):
                mod_name = mod_name.decode(u'utf_8')
            renpy_name = posixpath.normpath(u''.join((mod_name.replace(u'.', u'/'), cls.py_format))).replace(u'\\', u'/')
            if renpy.loader.loadable(renpy_name):
                return renpy_name
            renpy_name = posixpath.normpath(posixpath.join(mod_name.replace(u'.', u'/'), u'__init__{0}'.format(cls.py_format))).replace(u'\\', u'/')
            if renpy.loader.loadable(renpy_name):
                return renpy_name
            return None

        def find_spec(self, fullname, path=None, target=None):
            renpy_name = self.get_loadable_name(fullname)
            if renpy_name is None:
                return None
            return importlib.util.spec_from_loader(fullname, loader=self, origin=renpy_name)

        def find_module(self, fullname, path=None):
            renpy_name = self.get_loadable_name(fullname)
            if renpy_name is None:
                return None
            return self

        def load_module(self, fullname):
            renpy_name = self.get_loadable_name(fullname)
            if renpy_name is None:
                return None
            binary_data = self.get_data(renpy_name)
            binary_data = zlib.decompress(binary_data)
            binary_data = base64.b64decode(binary_data)
            ast_object = pickle.loads(binary_data)
            code = compile(ast_object, renpy_name, u'exec', compiler_flags, 1)
            mod = sys.modules.setdefault(fullname, types.ModuleType(fullname))
            mod.__name__ = fullname
            mod.__file__ = renpy_name
            mod.__loader__ = self
            basename, _ext = posixpath.splitext(posixpath.basename(posixpath.normpath(renpy_name)))
            if basename == u'__init__':
                mod.__path__ = builtins.list()
                _path = posixpath.dirname(posixpath.normpath(renpy_name.replace(u'\\', u'/')))
                _path = u'{0}/'.format(_path.replace(u'\\', u'/'))
                mod.__path__.append(_path)
            exec(code, mod.__dict__)
            return sys.modules[fullname]

        def get_data(self, filename):
            if isinstance(filename, bytes):
                filename = filename.decode(u'utf_8')

            def _open_func(fn):
                if hasattr(renpy, u'open_file'):
                    return renpy.open_file(fn, False)
                return renpy.file(fn)
            filename = posixpath.normpath(filename.replace(u'\\', u'/')).replace(u'\\', u'/')
            with _open_func(filename) as _file:
                return _file.read()
    sys.meta_path.append(PyLoader())









init -8 python in _translator3000:
    class Restart(Exception):
        pass


    class Preparer(threading.Thread, SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'Preparer')
        PRESCAN_COOLDOWN = None

        def __init__(self, translator_object):
            if self.initialized:
                return
            super(Preparer, self).__init__()
            self.daemon = True
            self._translator = translator_object
            self._m1_0x3ctranslator30000x3e__base_downloader = BaseDownloader(translator_object=self._translator)
            self._m1_0x3ctranslator30000x3e__state = None
            self._m1_0x3ctranslator30000x3e__status = None
            self._m1_0x3ctranslator30000x3e__completed = False
            self._m1_0x3ctranslator30000x3e__last_exception = None
            self._switcher = False
            self._m1_0x3ctranslator30000x3e__need_restart = True
            self._m1_0x3ctranslator30000x3e__last_prescan = None
            self._variables = builtins.set()
            self._m1_0x3ctranslator30000x3e__sort_keys_mapping = builtins.dict()
            self.initialized = True

        @property
        def base_downloader(self):
            return self._m1_0x3ctranslator30000x3e__base_downloader

        def restart(self):
            self.LOGGER.debug('Restart of prescan thread has been requested.')
            self._m1_0x3ctranslator30000x3e__need_restart = True
            self.state = u'reloading'

        def get_info(self):
            done = total = symbols = strings = 0
            status = 0.0
            if self._m1_0x3ctranslator30000x3e__status:
                done, total, symbols, strings = self._m1_0x3ctranslator30000x3e__status
                if total > 0:
                    status = float(done) / float(total)
            return __renpy__dict__({u'done': done, u'total': total, u'status': status, u'symbols': symbols, u'strings': strings})

        @staticmethod
        def _restart_interaction_and_wait(wait_time=0.01):
            renpy.restart_interaction()
            time.sleep(wait_time)

        @property
        def state(self):
            return self._m1_0x3ctranslator30000x3e__state

        @state.setter
        def state(self, new_val):
            self._m1_0x3ctranslator30000x3e__state = new_val
            self._restart_interaction_and_wait()

        @property
        def status(self):
            info = self.get_info()
            return info[u'status']

        def is_completed(self):
            return self._m1_0x3ctranslator30000x3e__completed

        def has_exception(self):
            if isinstance(self._m1_0x3ctranslator30000x3e__last_exception, Exception):
                return True
            return False

        def _raise_from_thread(self):
            if self.has_exception():
                raise self._m1_0x3ctranslator30000x3e__last_exception

        def _m1_0x3ctranslator30000x3e__get_all_unchecked_raw_text(self):
            self.LOGGER.debug(u'Text scanning is started.')
            _lang = _preferences.language
            _renpy_translator = renpy.game.script.translator
            _string_translator = _default_translator = None
            if _lang in _renpy_translator.strings:
                _string_translator = _renpy_translator.strings[_lang]
            if None in _renpy_translator.strings:
                _default_translator = _renpy_translator.strings[None]
            _unpack_types = renpy.ast.UserStatement, renpy.ast.Translate

            def _is_translatesay(node):
                if not hasattr(renpy.ast, u'TranslateSay'):
                    return False
                if isinstance(node, renpy.ast.TranslateSay):
                    return True
                return False

            def _get_say_nodes_from_node(node):
                if _is_translatesay(node):
                    _lookup = node.lookup()
                    if _lookup is None or _lookup is node:
                        yield node
                    else:
                        for say_node in _get_say_nodes_from_node(_lookup):
                            yield say_node
                elif isinstance(node, renpy.ast.Say):
                    yield node
                elif isinstance(node, _unpack_types):
                    for child_node in node.predict():
                        for say_node in _get_say_nodes_from_node(child_node):
                            yield say_node
            self.LOGGER.debug(u'Dialogue scanning.')
            for _node in _renpy_translator.default_translates.values():
                for say_node in _get_say_nodes_from_node(_node):
                    self._m1_0x3ctranslator30000x3e__sort_keys_mapping[say_node.what] = 0, say_node.filename, say_node.linenumber
                    yield say_node.what
            self.LOGGER.debug(u'UI translations scanning (1/2).')
            if _string_translator:
                for string in _string_translator.translations.values():
                    yield string
            self.LOGGER.debug(u'UI translations scanning (2/2).')
            if _default_translator:
                for k, string in _default_translator.translations.items():
                    if _string_translator:
                        if k in _string_translator.translations:
                            continue
                    yield string
            self.LOGGER.debug(u'Choices menu is scanned.')
            for _data in _renpy_translator.additional_strings.values():
                for _i, string in _data:
                    if _string_translator:
                        if string in _string_translator.translations:
                            continue
                    yield string
            self.LOGGER.debug(u'Other strings is scanned.')
            for string_obj in renpy.translation.scanstrings.scan(min_priority=-1e999, max_priority=1e999, common_only=False):
                if _string_translator:
                    if string_obj.text in _string_translator.translations:
                        continue
                _key = (2,) + string_obj.sort_key
                self._m1_0x3ctranslator30000x3e__sort_keys_mapping[string_obj.text] = _key
                yield string_obj.text
            self.LOGGER.debug(u'Text has been scanned.')

        @staticmethod
        def _get_variables_from_string(_string):
            for _search in re.finditer(u'%\\((?P<key>[\\w\\.]+)\\)[a-z]', _string, flags=re.UNICODE | re.DOTALL):
                yield _search.group(u'key')
            for _search in re.finditer(u'\\[(?P<key>[\\w.]+)\\]', _string, flags=re.UNICODE | re.DOTALL):
                yield _search.group(u'key')

        def _get_all_raw_text(self, _set_variables=True):
            result = builtins.list()
            for _string in self._m1_0x3ctranslator30000x3e__get_all_unchecked_raw_text():
                if not isinstance(_string, basestring):
                    continue
                string = utils.Encoding.utf8decode(_string)
                string = string.strip()
                if not string:
                    continue
                if _string in self._m1_0x3ctranslator30000x3e__sort_keys_mapping:
                    self._m1_0x3ctranslator30000x3e__sort_keys_mapping[string] = self._m1_0x3ctranslator30000x3e__sort_keys_mapping[_string]
                result.append(string)
                if _set_variables:
                    self._variables.update(self._get_variables_from_string(string))
            return frozenset(result)

        def get_all_unquoted_and_croped_strings(self, raw_text=None):
            if raw_text is None:
                raw_text = self._get_all_raw_text()
            result = builtins.set()
            for r_txt in raw_text:
                txt = self._translator.unquote(r_txt)
                txt = self._translator._crop_string(txt)
                if txt:
                    if r_txt in self._m1_0x3ctranslator30000x3e__sort_keys_mapping:
                        self._m1_0x3ctranslator30000x3e__sort_keys_mapping[txt] = self._m1_0x3ctranslator30000x3e__sort_keys_mapping[r_txt]
                    result.add(txt)
            return frozenset(result)

        def _need_translate(self, text):
            _is_translated = self._translator.string_is_translated(text, _need_unquote=False, _need_crop=False)
            return not _is_translated

        def _get_string_len(self, text):
            return self._translator.get_string_len(text, _need_unquote=False)

        def get_translate_parts(self, strings_array, only_not_translated=True, _use_fast_logic=False):

            def _sort_key(value):
                if self._translator._setting[u'alternativeSortMethod']:
                    if value in self._m1_0x3ctranslator30000x3e__sort_keys_mapping:
                        return self._m1_0x3ctranslator30000x3e__sort_keys_mapping[value]
                return (1, self._get_string_len(value))
            check_func = lambda _a: True
            if only_not_translated:
                check_func = self._need_translate
            self.LOGGER.debug('Combining strings for parts.')
            need_translate_strings = builtins.list(builtins.sorted(tuple(filter(check_func, frozenset(strings_array))), key=_sort_key, reverse=True))
            self.LOGGER.debug('Creating parts.')
            while True:
                if not need_translate_strings:
                    break
                strings_for_translate = self.get_strings_for_translate(need_translate_strings, _use_fast_logic)
                for s in strings_for_translate:
                    need_translate_strings.remove(s)
                yield u'\n\n\n'.join(strings_for_translate)

        def get_strings_for_translate(self, sorted_array, _use_fast_logic=False):
            _limit = float(self._translator.get_translate_symb_limit())
            if _limit < 10.0:
                raise RuntimeError(u'\u041d\u0435\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u043b\u0438\u043c\u0438\u0442 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432.')
            max_size = _limit - 1.0
            if _use_fast_logic:
                min_size = max(max_size - 1000.0, 5.0)
            else:
                min_size = max(max_size - 250.0, 5.0)
            string_pool = builtins.list(sorted_array[:])
            result = builtins.list()
            while True:
                _result_len = self._get_string_len(u'\n\n\n'.join(result))
                if min_size <= _result_len <= max_size:
                    return result
                elif _result_len >= max_size:
                    if not result:
                        raise RuntimeError(u'len func is incorrect.')
                    elif len(result) == 1:
                        return result
                    result.pop(-1)
                    continue
                if not string_pool:
                    return result
                result.append(string_pool.pop(-1))

        def _switcher_or_restart_wait(self):
            while True:
                if self._m1_0x3ctranslator30000x3e__need_restart:
                    raise Restart()
                if self._switcher:
                    return
                time.sleep(0.5)

        def run(self):
            while True:
                while True:
                    if self._m1_0x3ctranslator30000x3e__need_restart:
                        break
                    if self._m1_0x3ctranslator30000x3e__last_prescan is None:
                        break
                    if self.PRESCAN_COOLDOWN is not None:
                        passed_time = time.time() - self._m1_0x3ctranslator30000x3e__last_prescan
                        if passed_time >= self.PRESCAN_COOLDOWN:
                            break
                    time.sleep(1.0)
                self._m1_0x3ctranslator30000x3e__need_restart = False
                self._m1_0x3ctranslator30000x3e__status = None
                self._m1_0x3ctranslator30000x3e__completed = False
                self._m1_0x3ctranslator30000x3e__last_exception = None
                try:
                    self.LOGGER.debug('Check remote DB server.')
                    self.state = u'check_remote_db'
                    self._switcher_or_restart_wait()
                    game_version = self.base_downloader.get_game_version()
                    _u_srvs = self.base_downloader.find_and_set_db_package()
                    extra = None
                    if isinstance(_u_srvs, tuple) and len(_u_srvs) == 2:
                        _u_srvs, extra = _u_srvs
                    tr = self._translator
                    stng = tr._setting
                    if _u_srvs:
                        if tr._translationService in _u_srvs:
                            self.LOGGER.debug('Found prepared DB for current service.')
                        elif stng[u'autoSwitchOnAvailableDB']:
                            _change_action = tr._gui.ApplySettingAction(language_check=True)
                            for srv in (u'reverso', u'google_gtx', u'yandex', u'lingvanex'):
                                if srv in _u_srvs:
                                    tr._translationService = srv
                                    renpy.run(_change_action)
                                    self.LOGGER.debug('Found prepared DB for "%s". Changed.', srv)
                                    self._translator.popup_windows_handler.show_info(u'\u041d\u0430\u0439\u0434\u0435\u043d\u0430 \u0433\u043e\u0442\u043e\u0432\u0430\u044f \u0411\u0414 \u0432 \u043e\u0431\u043b\u0430\u043a\u0435. \u0421\u0435\u0440\u0432\u0438\u0441 \u0438\u0437\u043c\u0435\u043d\u0451\u043d \u043d\u0430 "{service_name}"', u'\u0421\u0435\u0440\u0432\u0438\u0441 \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0430 \u0438\u0437\u043c\u0435\u043d\u0451\u043d', _raise=False, service_name=srv)
                    self.LOGGER.debug('Preparing a pre-scan thread.')
                    self.state = u'assembling'
                    self._switcher_or_restart_wait()
                    self._variables = builtins.set()
                    all_raw_text = self._get_all_raw_text(True)
                    if stng[u'addVariablesFromDB']:
                        self.LOGGER.debug('Set variables.')
                        if extra and extra[u'variables']:
                            for k, v in extra[u'variables'].items():
                                if k in self._variables:
                                    try:
                                        VarsChanger._set_value(k, v)
                                    except Exception as ex:
                                        self.LOGGER.exception(ex)
                                        continue
                        else:
                            self.LOGGER.debug('No variables was found.')
                    all_strings = self.get_all_unquoted_and_croped_strings(all_raw_text)
                    symbols_len = sum(map(len, all_strings))
                    strings_len = len(all_strings)
                    self._translator._stat_object._update_value(u'symbols_len', symbols_len)
                    self._translator._stat_object._update_value(u'strings_len', strings_len)
                    for _state in (u'first_scan', u'working', u'finalizing'):
                        self.state = u'assembling'
                        _use_fast_logic = False
                        only_not_translated = True
                        _no_raise = False
                        if _state == u'finalizing':
                            _use_fast_logic = True
                            only_not_translated = False
                        elif _state == u'first_scan':
                            _no_raise = True
                        self.LOGGER.debug('Preparation of %s.', _state)
                        self._m1_0x3ctranslator30000x3e__status = 0, 0, symbols_len, strings_len
                        parts = builtins.set()
                        for done, part in enumerate(self.get_translate_parts(all_strings, only_not_translated, _use_fast_logic), 1):
                            self.state = u'scanning'
                            self._switcher_or_restart_wait()
                            parts.add(part)
                            self._m1_0x3ctranslator30000x3e__status = done, 0, symbols_len, strings_len
                            self._restart_interaction_and_wait()
                        self.state = u'preparing'
                        parts = frozenset(parts)
                        total = len(parts)
                        self._m1_0x3ctranslator30000x3e__status = 0, total, symbols_len, strings_len
                        self.state = _state
                        self.LOGGER.debug('%s state is started.', _state)
                        for done, text_strings in enumerate(parts):
                            self._switcher_or_restart_wait()
                            self._m1_0x3ctranslator30000x3e__status = done, total, symbols_len, strings_len
                            self._restart_interaction_and_wait()
                            self._translator(text_strings, _force=True, _need_unquote=False, _need_crop=False, _is_prescan=True, check_db_first=False, _no_raise=_no_raise)
                except translator_abstract.SymbolLimitExceeded:
                    self.LOGGER.debug('The character limit has changed. String recalculation is started.')
                    self._m1_0x3ctranslator30000x3e__need_restart = True
                except Restart:
                    self._m1_0x3ctranslator30000x3e__need_restart = True
                except Exception as ex:
                    if not self._m1_0x3ctranslator30000x3e__need_restart:
                        self.LOGGER.exception(ex)
                        self._m1_0x3ctranslator30000x3e__last_exception = ex
                else:
                    self.state = u'almost_done'
                    if not self._m1_0x3ctranslator30000x3e__need_restart:
                        self.LOGGER.debug('Creation DB package is started.')
                        try:
                            package_name = self.base_downloader.create_distribution_package(self._variables, _upload=True)
                        except Exception as ex:
                            package_name = None
                            self.LOGGER.exception(ex)
                        else:
                            self.LOGGER.debug('Successful.')
                        self._m1_0x3ctranslator30000x3e__completed = True
                        self.LOGGER.debug('Pre-scan is complete.')
                        _k = u'startTranslateAfterPrescan'
                        if self._translator._setting[_k]:
                            self._translator._gui.mode = u'db_only'
                        self.show_popup_after_prescan(package_name)
                finally:
                    self._translator.backup_database()
                    self.state = u'done'
                    self._m1_0x3ctranslator30000x3e__status = None
                    self._m1_0x3ctranslator30000x3e__last_prescan = time.time()
                    self._restart_interaction_and_wait()

        def show_popup_after_prescan(self, package_name=None):
            if not (isinstance(package_name, basestring) and path.isfile(package_name)):
                self._translator.popup_windows_handler.show_info(u'\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0437\u0430\u043a\u043e\u043d\u0447\u0435\u043d\u043e', u'\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435', _raise=False)
                return

            def _yes_function():
                txt = u'\u041e\u0442\u043b\u0438\u0447\u043d\u043e!\n\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u0430\u0439\u043b "{name_only}" (\u043f\u0430\u043f\u043a\u0430 \u0441 \u0444\u0430\u0439\u043b\u043e\u043c \u0434\u043e\u043b\u0436\u043d\u0430 \u0431\u044b\u043b\u0430 \u043e\u0442\u043a\u0440\u044b\u0442\u044c\u0441\u044f \u0432 \u0444\u043e\u043d\u0435) \u0432 Telegram \u043a\u0430\u043d\u0430\u043b \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0447\u0438\u043a\u0430 (\u0441\u0441\u044b\u043b\u043a\u0430 \u0434\u043e\u043b\u0436\u043d\u0430 \u0431\u044b\u043b\u0430 \u043e\u0442\u043a\u0440\u044b\u0442\u044c\u0441\u044f \u0432 \u0431\u0440\u0430\u0443\u0437\u0435\u0440\u0435 \u0438\u043b\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0438 Telegram).'
                self._translator.popup_windows_handler.show_info(txt, u'\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435', name_only=path.basename(package_name), _raise=False, create_thread=False, other_count=False)
            txt = u'''\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0437\u0430\u043a\u043e\u043d\u0447\u0435\u043d\u043e!
\u0421\u043e\u0437\u0434\u0430\u043d\u0430 \u0431\u0430\u0437\u0430 \u0434\u0430\u043d\u043d\u044b\u0445 \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0430 \u0438\u0433\u0440\u044b.

\u041f\u043e\u0434\u0435\u043b\u0438\u0442\u0435\u0441\u044c \u0433\u043e\u0442\u043e\u0432\u044b\u043c \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u043e\u043c \u0432 Telegram \u043a\u0430\u043d\u0430\u043b\u0435 \u0441 \u0434\u0440\u0443\u0433\u0438\u043c\u0438 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u043c\u0438, \u0447\u0442\u043e\u0431\u044b \u043e\u043d\u0438 \u043c\u043e\u0433\u043b\u0438 \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u043c\u0433\u043d\u043e\u0432\u0435\u043d\u043d\u044b\u0439 \u043f\u0435\u0440\u0435\u0432\u043e\u0434 \u044d\u0442\u043e\u0439 \u0438\u0433\u0440\u044b!

\u041f\u043e\u0434\u0435\u043b\u0438\u0442\u044c\u0441\u044f?'''
            self._translator.popup_windows_handler.show_info(txt, u'\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435', flags=self._translator.popup_windows_handler.MB_YESNO, _raise=False, action_IDYES=(store.OpenDirectory(path.dirname(package_name)), store.OpenURL(u'https://t.me/translator3000/26'), store.Function(_yes_function)))
























































































































init -11 python in _translator3000:
    GameInfo = collections.namedtuple(u'GameInfo', (u'game_id', u'game_name', u'icon', u'timer', u'symbols_len', u'strings_len', u'basedir', u'translations_db_dir'))


    class _GameTimer(SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'_GameTimer')
        LAST_DUMP = time.time()
        LOCK = threading.RLock()
        SECOND = 1.0
        MINUTE = 60.0 * SECOND
        HOUR = 60.0 * MINUTE
        DAY = 24.0 * HOUR
        MONTH = 30.0 * DAY

        def __init__(self, stat_object):
            if self.initialized:
                return
            self._stat_object = stat_object
            self.initialized = True

        @classmethod
        def convert_seconds_to_readable_form(cls, total_seconds):
            if isinstance(total_seconds, _GameTimer):
                total_seconds = total_seconds.game_time
            total_seconds = float(total_seconds)
            if total_seconds < 0.0:
                raise ValueError(total_seconds)
            months = total_seconds // cls.MONTH
            total_seconds -= months * cls.MONTH
            days = total_seconds // cls.DAY
            total_seconds -= days * cls.DAY
            hours = total_seconds // cls.HOUR
            total_seconds -= hours * cls.HOUR
            minutes = total_seconds // cls.MINUTE
            total_seconds -= minutes * cls.MINUTE
            seconds = total_seconds // cls.SECOND
            total_seconds -= seconds * cls.SECOND
            months, days, hours, minutes, seconds = map(int, (months, days, hours, minutes, seconds))
            parts = builtins.list()
            if months:
                parts.append(u'{0} months'.format(months))
            if days:
                parts.append(u'{0} days'.format(days))
            if hours:
                parts.append(u'{0} hours'.format(hours))
            if minutes:
                parts.append(u'{0} minutes'.format(minutes))
            if seconds:
                parts.append(u'{0} seconds'.format(seconds))
            if not parts:
                return u'0 seconds'
            return u' '.join(parts)

        @property
        def game_time(self):
            with self.LOCK:
                self._periodic_callback(True)
                return self._game_time

        @property
        def _game_time(self):
            with self.LOCK:
                return self._stat_object._current_data_dict.get(u'timer', 0.0)

        @_game_time.setter
        def _game_time(self, new_value):
            with self.LOCK:
                self._stat_object._current_data_dict[u'timer'] = new_value
                self._stat_object._translator._multi_persistent.save()

        def _periodic_callback(self, _force_update=False):
            with self.LOCK:
                _current = time.time()
                elapsed = _current - _GameTimer.LAST_DUMP
                if _force_update or elapsed >= 30.0:
                    self._game_time += elapsed
                    _GameTimer.LAST_DUMP = _current


    class Statistic(SingleTone):
        __author__ = u'Vladya'
        LOGGER = LOGGER.getChild(u'Statistic')
        ICONS_ZIP = _zip_handler.Zip(path.abspath(path.join(_paths.DATABASE_FOLDER, u'icons.tr3000_img')))
        LOCK = threading.RLock()

        def __init__(self, translator_object):
            if self.initialized:
                return
            self._translator = translator_object
            _mp = self._translator._multi_persistent
            if _mp.statistic is None:
                _mp.statistic = builtins.dict()
            self._current_data_dict[u'game_name'] = self._get_current_name()
            if u'icon' not in self._current_data_dict:
                self._current_data_dict[u'icon'] = None
            with Statistic.LOCK:
                _current_icon = self._get_current_icon()
                if isinstance(_current_icon, im.Data):
                    Statistic.ICONS_ZIP.add_file(arch_name=_current_icon.filename, fo_or_bytes=_current_icon.data, rewrite=True, is_fo=False)
                    self._current_data_dict[u'icon'] = _current_icon.filename
            if u'timer' not in self._current_data_dict:
                self._current_data_dict[u'timer'] = 0.0
            self._timer = _GameTimer(stat_object=self)
            if u'symbols_len' not in self._current_data_dict:
                self._current_data_dict[u'symbols_len'] = None
            if u'strings_len' not in self._current_data_dict:
                self._current_data_dict[u'strings_len'] = None
            if u'pathes' not in self._current_data_dict:
                self._current_data_dict[u'pathes'] = builtins.dict()
            self._current_data_dict[u'pathes'][u'basedir'] = path.abspath(renpy.config.basedir)
            self._current_data_dict[u'pathes'][u'translations_db_dir'] = _paths.TRANSLATIONS_DB_DIR
            _mp.save()
            self._gamelist = None
            self.initialized = True

        def _periodic_callback(self):
            self._timer._periodic_callback()

        @property
        def _current_id(self):
            return config.save_directory

        @property
        def _current_data_dict(self):
            _mp = self._translator._multi_persistent
            if self._current_id not in _mp.statistic:
                _mp.statistic[self._current_id] = builtins.dict()
                _mp.save()
            return _mp.statistic[self._current_id]

        @property
        def game_list(self):
            with Statistic.LOCK:
                if self._gamelist is None:
                    self._gamelist = self._get_all_games()
                return self._gamelist

        @property
        def current_game(self):
            with Statistic.LOCK:
                for _game in self.game_list:
                    if _game.game_id == self._current_id:
                        return _game
                raise RuntimeError(u'Game not found')

        def _update_value(self, field_name, new_value):
            with Statistic.LOCK:
                if field_name not in self._current_data_dict:
                    raise ValueError(field_name)
                self._current_data_dict[field_name] = new_value
                self._translator._multi_persistent.save()
                self._gamelist = None

        def _get_all_games(self):
            _mp = self._translator._multi_persistent
            result = builtins.list()
            with Statistic.LOCK, _mp.lock:
                for _game_id, game_data in _mp.statistic.items():
                    icon = game_data[u'icon']
                    if icon is not None:
                        try:
                            icon = im.Data(Statistic.ICONS_ZIP.read_file(icon), icon)
                        except Exception as ex:
                            self.LOGGER.exception(ex)
                            icon = None
                    timer = game_data[u'timer']
                    if _game_id == self._current_id:
                        timer = self._timer
                    basedir = None
                    translations_db_dir = None
                    if u'pathes' in game_data:
                        if u'basedir' in game_data[u'pathes']:
                            basedir = game_data[u'pathes'][u'basedir']
                        if u'translations_db_dir' in game_data[u'pathes']:
                            basedir = game_data[u'pathes'][u'translations_db_dir']
                    game = GameInfo(game_id=_game_id, game_name=game_data[u'game_name'], icon=icon, timer=timer, symbols_len=game_data[u'symbols_len'], strings_len=game_data[u'strings_len'], basedir=basedir, translations_db_dir=translations_db_dir)
                    result.append(game)
            return tuple(result)

        @staticmethod
        def _get_current_name():
            NONAME = u"A Ren'Py Game"
            if config.name is not None:
                _game_name = config.name.strip()
                if _game_name and _game_name != NONAME:
                    return _game_name
            if config.window_title is not None:
                _game_name = config.window_title.strip()
                if _game_name and _game_name != NONAME:
                    return _game_name
            if build.name is not None:
                _game_name = build.name.strip()
                if _game_name and _game_name != NONAME:
                    return _game_name
            if config.save_directory is not None:
                _game_name = config.save_directory.strip()
                if _game_name and _game_name != NONAME:
                    return _game_name
            return NONAME

        def _get_current_icon(self):
            if not config.window_icon:
                return None
            try:
                ext = utils.get_ext(config.window_icon)
                fn = u''.join((self._current_id, ext))
                with utils.renpy_open(config.window_icon) as _icon:
                    im_data = im.Data(_icon.read(), fn)
            except Exception as ex:
                self.LOGGER.exception(ex)
                return None
            else:
                return im_data

        @staticmethod
        def _calculate_icon_zoom(im_data):
            _f = store._translator3000_gui.GUILoader._calculate_zoom
            return _f(im_data, 50.0)

















init -7 python in _translator3000:
    class VarWrapper(store.FieldEquality, store.NoRollback):
        __author__ = u'Vladya'
        IGNORED_INSTANCES = renpy.python.StoreDict, renpy.python.StoreModule, type(random)
        IGNORE_TYPES = ()
        IGNORE_CALLABLES = True
        FILE_LOCK = threading.RLock()
        VARIABLES_FILES_DEFINITION_CACHE = None
        equality_fields = u'_parent', u'_name', u'_name_as_index', u'_var_name', u'_store_data'
        identity_fields = u'_property_changeable',

        def __init__(self, parent, name, name_as_index=False, var_name=None, store_data=None, property_changeable=None):
            self._parent = parent
            self._name = name
            self._name_as_index = name_as_index
            self._var_name = var_name
            self._store_data = store_data
            self._property_changeable = property_changeable

        @property
        def favorite(self):
            if self.var_name in persistent.tr3000_favorite_variables:
                return True
            return False

        @favorite.setter
        def favorite(self, new_value):
            if new_value:
                _new_arr = persistent.tr3000_favorite_variables.union((self.var_name,))
            else:
                _new_arr = persistent.tr3000_favorite_variables.difference((self.var_name,))
            persistent.tr3000_favorite_variables = _new_arr

        def is_property(self):
            if self._property_changeable is True:
                return True
            if self._property_changeable is False:
                return True
            return False

        def is_changeable(self):
            if not self.is_property():
                return True
            if self._property_changeable is True:
                return True
            return False

        def is_root(self):
            if isinstance(self._parent, VarWrapper):
                return False
            return True

        def _is_showed_value(self):
            try:
                value = self.value
            except Exception:
                return False
            if self.IGNORE_CALLABLES and callable(value):
                return False
            if isinstance(value, self.IGNORED_INSTANCES):
                return False
            for _IgnoreType in self.IGNORE_TYPES:
                if type(value) is _IgnoreType:
                    return False
            if self._var_name:
                name = self._var_name
            elif self._name_as_index:
                return True
            else:
                name = unicode(self._name)
            if u'translator3000' in name.lower():
                return False
            for pattern in VarsChanger.BLACKLIST_PATTERNS:
                if pattern.search(name):
                    return False
            if name.startswith(u'__'):
                return False
            if name in _RENPY_RESERVED_CONSTS:
                return False
            return True

        def walk(self, max_deep=None):
            if max_deep is None or max_deep > 0:
                max_deep = None if max_deep is None else max_deep - 1
                for child in self.get_children():
                    if not child._is_showed_value():
                        continue
                    yield child
                    for child_of_child in child.walk(max_deep):
                        yield child_of_child

        @property
        def parents(self):
            if self.is_root():
                return ()
            return (self._parent,) + self._parent.parents

        def get_children(self):
            val = self.value
            if isinstance(val, (tuple, builtins.list)):
                for i, _value in enumerate(val):
                    yield VarWrapper(self, i, name_as_index=True)
            elif isinstance(val, (builtins.set, frozenset)):
                for i, _value in enumerate(sorted(val, key=repr)):
                    yield VarWrapper(self, i, name_as_index=True)
            elif isinstance(val, (builtins.dict, collections.OrderedDict)):
                for k in sorted(val.keys(), key=repr):
                    yield VarWrapper(self, k, name_as_index=True)
            else:
                try:
                    dct = vars(val)
                except Exception:
                    pass
                else:
                    for k in sorted(dct.keys(), key=repr):
                        yield VarWrapper(self, k)
                try:
                    for _tps in val.__class__.mro():
                        try:
                            dct = vars(_tps)
                        except Exception:
                            continue
                        else:
                            for k, v in dct.items():
                                if isinstance(v, property):
                                    changeable = bool(getattr(v, u'fset', None))
                                    yield VarWrapper(self, k, property_changeable=changeable)
                except Exception:
                    pass

        def get_name_parts(self, add_null_dir=False):
            if self.is_root():
                parts = self.var_name.split(u'.')
                if parts[0] == u'store':
                    parts = parts[1:]
                parts = (u'.'.join(parts), self),
                if add_null_dir:
                    parts = ((u'//', None),) + parts
                return parts
            parts = self._parent.get_name_parts(add_null_dir)
            parts += (unicode(self._name), self),
            return parts

        @property
        def last_name_part(self):
            name, _instance = self.get_name_parts()[-1]
            return name

        def mark_as_changed(self):
            store_name, name = self.store_data
            store_dict = renpy.python.store_dicts.get(store_name, None)
            if store_dict:
                store_dict.ever_been_changed.add(name)

        def is_ever_been_changed(self):
            store_name, name = self.store_data
            store_dict = renpy.python.store_dicts.get(store_name, None)
            if not store_dict:
                return False
            if name in store_dict.ever_been_changed:
                return True
            return False

        def get_file_definition(self):
            with VarWrapper.FILE_LOCK:
                if VarWrapper.VARIABLES_FILES_DEFINITION_CACHE is None:
                    res = builtins.dict()
                    for stmt in renpy.game.script.all_stmts:
                        if hasattr(stmt, u'code') and hasattr(stmt, u'store'):
                            source, _location = stmt.code.__getstate__()[1:3]
                            filename = _location[0]
                            if not isinstance(filename, basestring):
                                continue
                            if hasattr(stmt, u'varname'):
                                res[stmt.store, stmt.varname] = filename
                            elif isinstance(source, basestring):
                                for _match_result in re.finditer(u'(^|\\n)\\s*(?P<name>\\w+)\\s*=\\s*\\S+', source):
                                    res[stmt.store, _match_result.group(u'name')] = filename
                    VarWrapper.VARIABLES_FILES_DEFINITION_CACHE = res
                return VarWrapper.VARIABLES_FILES_DEFINITION_CACHE.get(self.store_data, None)

        @property
        def store_data(self):
            if self._store_data:
                return self._store_data
            return self._parent.store_data

        @property
        def var_name(self):
            if self._var_name:
                return self._var_name
            if self.is_root():
                var_name = repr(self._parent)
            else:
                var_name = self._parent.var_name
            if self._name_as_index:
                var_name += u'[{0!r}]'.format(self._name)
            else:
                var_name += u'.{0}'.format(self._name)
            return var_name

        @property
        def value(self):
            parent_value = self._parent
            if not self.is_root():
                parent_value = parent_value.value
            if self._name_as_index:
                if isinstance(parent_value, (builtins.set, frozenset)):
                    parent_value = tuple(sorted(parent_value, key=repr))
                return parent_value[self._name]
            return getattr(parent_value, self._name)

        @value.setter
        def value(self, new_value):
            parent_value = self._parent
            if not self.is_root():
                parent_value = parent_value.value
            if self._name_as_index:
                if isinstance(parent_value, (tuple, frozenset)):
                    if not isinstance(self._parent, VarWrapper):
                        raise RuntimeError(u'Try to change {0!r} object.'.format(type(self._parent)))
                    _temp_parent = parent_value
                    if isinstance(_temp_parent, frozenset):
                        _temp_parent = sorted(_temp_parent, key=repr)
                    _temp_parent = builtins.list(_temp_parent)
                    _temp_parent[self._name] = new_value
                    if isinstance(parent_value, tuple):
                        _temp_parent = tuple(_temp_parent)
                    else:
                        _temp_parent = frozenset(_temp_parent)
                    self._parent.value = _temp_parent
                elif isinstance(parent_value, builtins.set):
                    _temp_parent = tuple(sorted(parent_value, key=repr))
                    value = _temp_parent[self._name]
                    parent_value.discard(value)
                    parent_value.add(new_value)
                else:
                    parent_value[self._name] = new_value
            else:
                setattr(parent_value, self._name, new_value)
            self.mark_as_changed()


    class SearchDaemon(threading.Thread, store.NoRollback):
        __author__ = u'Vladya'
        INPUT_ID = u':search_input:'
        TYPE_WAIT = 1.0
        LOGGER = LOGGER.getChild(u'SearchDaemon')

        def __init__(self, parent):
            super(SearchDaemon, self).__init__()
            self.daemon = True
            self._m1_0x3ctranslator30000x3e__parent = parent
            self._search_result = ()
            self._m1_0x3ctranslator30000x3e__current_pattern = u''
            self._m1_0x3ctranslator30000x3e__flags = re.UNICODE | re.IGNORECASE
            self._m1_0x3ctranslator30000x3e__change_time = None
            self._m1_0x3ctranslator30000x3e__restart_flag = False
            self._pause = True

        def restart_search(self, set_pause=None):
            with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                self._m1_0x3ctranslator30000x3e__restart_flag = True
                if set_pause is not None:
                    self._pause = bool(set_pause)

        @property
        def search_pattern(self):
            with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                return self._m1_0x3ctranslator30000x3e__current_pattern

        @search_pattern.setter
        def search_pattern(self, new_pattern):
            with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                self._m1_0x3ctranslator30000x3e__current_pattern = new_pattern
                self._m1_0x3ctranslator30000x3e__parent.set_search_mode(bool(new_pattern.strip()))
                self._m1_0x3ctranslator30000x3e__change_time = time.time()
                self.restart_search(set_pause=not new_pattern.strip())

        def _m1_0x3ctranslator30000x3e__get_search_results(self, search_names=True, search_values=True):
            if search_names or search_values:
                with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                    variables_groups = self._m1_0x3ctranslator30000x3e__parent.get_vars_for_search()
                    search_pattern = self.search_pattern
                if variables_groups and search_pattern.strip():
                    pattern = re.compile(search_pattern, flags=self._m1_0x3ctranslator30000x3e__flags)
                    for group_name, variables_group in variables_groups:
                        for var_wrapper in variables_group:
                            self.wait_pause()
                            _where = builtins.list()
                            if search_names:
                                _where.append(var_wrapper.last_name_part)
                            if search_values:
                                _val = var_wrapper.value
                                if isinstance(_val, (unicode, long, int, complex, float)):
                                    _where.append(unicode(_val))
                            for _search_data in _where:
                                try:
                                    _match_result = pattern.search(_search_data)
                                except Exception:
                                    continue
                                if _match_result:
                                    yield var_wrapper
                                    break

        def wait_pause(self):
            while True:
                with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                    if self._m1_0x3ctranslator30000x3e__restart_flag:
                        raise Restart()
                    if not self._pause:
                        if self._m1_0x3ctranslator30000x3e__change_time is None:
                            return
                        elapsed = time.time() - self._m1_0x3ctranslator30000x3e__change_time
                        if elapsed >= self.TYPE_WAIT:
                            return
                time.sleep(0.1)

        def run(self):
            while True:
                self._m1_0x3ctranslator30000x3e__restart_flag = False
                if self._search_result:
                    self._search_result = ()
                    self._m1_0x3ctranslator30000x3e__parent._reset_current_wrapper()
                try:
                    self.wait_pause()
                    for var_wrapper in self._m1_0x3ctranslator30000x3e__get_search_results():
                        self._search_result += var_wrapper,
                        self._m1_0x3ctranslator30000x3e__parent._reset_current_wrapper()
                    with self._m1_0x3ctranslator30000x3e__parent._set_lock:
                        self._pause = True
                    self.wait_pause()
                except Restart:
                    continue
                except Exception as ex:
                    self.LOGGER.exception(ex)


    class VarsChanger(store.NoRollback):
        __author__ = u'Vladya'
        _STRING_REPR_LIMIT = 20
        _ELEMENTS_OF_PAGE_LIMIT = 25
        DEEP_OF_SCAN = 3
        SEARCH_PATTERNS = builtins.dict()
        BLACKLIST_PATTERNS = tuple(map(lambda ptr: re.compile(u'(?<![a-z])({0})(?![a-z])'.format(u'|'.join(ptr)), flags=re.IGNORECASE | re.UNICODE), ()))
        VARIABLES_LOCK = threading.RLock()
        ROOT_INSTANCES_CACHE = None
        INCREMENT_STEP_POW = 0
        LOGGER = LOGGER.getChild(u'VarsChanger')

        def __init__(self, _translator_object):
            self._create_search_patterns()
            self._set_lock = threading.RLock()
            self._current_pages = builtins.dict()
            self._current_wrapper = None
            self._current_page = 0
            self._m1_0x3ctranslator30000x3e__current_input_id = None
            self.max_page_index = 0
            self.variables_groups = None
            self._search_daemon = SearchDaemon(self)
            self._translator_object = _translator_object
            self._m1_0x3ctranslator30000x3e__active = True
            self._m1_0x3ctranslator30000x3e__search_mode = False
            if renpy.game.context().init_phase:
                renpy.game.post_init.append(self._search_daemon.start)
            else:
                self._search_daemon.start()

        def set_search_mode(self, new_value):
            with self._set_lock:
                old_value = self._m1_0x3ctranslator30000x3e__search_mode
                self._m1_0x3ctranslator30000x3e__search_mode = new_value
                if new_value != old_value:
                    self.set_wrapper(_SameWrapper, reset_input_id=False)

        @property
        def current_input_id(self):
            with self._set_lock:
                return self._m1_0x3ctranslator30000x3e__current_input_id

        @current_input_id.setter
        def current_input_id(self, new_value):
            with self._set_lock:
                self._m1_0x3ctranslator30000x3e__current_input_id = new_value
                if new_value == SearchDaemon.INPUT_ID:
                    self._search_daemon._pause = False
                else:
                    self._search_daemon._pause = True

        @property
        def visible_groups_for_screen(self):
            with self._set_lock:
                result = self.variables_groups
                if not result:
                    return ((None, ()),)
                return result

        def _screen_init(self):
            with self._set_lock:
                self.set_wrapper(None, 0)

        def is_active(self):
            return self._m1_0x3ctranslator30000x3e__active

        def _reset_current_wrapper(self):
            with self._set_lock:
                self.set_wrapper(_SameWrapper, self._current_page, False)

        def set_wrapper(self, wrapper, page=None, reset_input_id=True):
            with self._set_lock:
                if not self.is_active():
                    return
                if reset_input_id:
                    self.current_input_id = None
                if wrapper is _SameWrapper:
                    wrapper = self._current_wrapper
                else:
                    self._search_daemon.search_pattern = u''
                if self._m1_0x3ctranslator30000x3e__search_mode:
                    if page is None or wrapper is not self._current_wrapper:
                        page = 0
                else:
                    _key = None if wrapper is None else wrapper.var_name
                    if page is None:
                        page = self._current_pages.get(_key, 0)
                    if wrapper is None:
                        self._current_pages.clear()
                    self._current_pages[_key] = page
                self._current_wrapper = wrapper
                self._current_page = page
                self.max_page_index = 0
                self.variables_groups = None
                th = threading.Thread(target=self._set_vars_for_screen, kwargs=builtins.dict(wrapper=self._current_wrapper, page=self._current_page, is_search_mode=self._m1_0x3ctranslator30000x3e__search_mode))
                th.daemon = True
                self._m1_0x3ctranslator30000x3e__active = False
                th.start()

        def set_page(self, page):
            with self._set_lock:
                return self.set_wrapper(_SameWrapper, page)

        def _set_vars_for_screen(self, wrapper, page, is_search_mode):
            try:
                if is_search_mode:
                    max_page_index, variables_groups = self.sorted_and_crop(((self._translator_object._gui.translate(u'\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u043f\u043e\u0438\u0441\u043a\u0430', not_translate_mark=False), self._search_daemon._search_result),), current_page=page, add_favorite_group=True)
                else:
                    max_page_index, variables_groups = self.get_vars_from_wrapper(wrapper, page)
                with self._set_lock:
                    self._current_wrapper = wrapper
                    self._current_page = page
                    self.max_page_index = max_page_index
                    self.variables_groups = variables_groups
            except Exception as ex:
                self.LOGGER.exception(ex)
            finally:
                self._m1_0x3ctranslator30000x3e__active = True
            renpy.restart_interaction()

        def clear_cache(self):
            with VarsChanger.VARIABLES_LOCK, self._set_lock:
                VarsChanger.ROOT_INSTANCES_CACHE = None
                self._current_wrapper = None
                self._current_page = 0
                self.current_input_id = None
                self._m1_0x3ctranslator30000x3e__search_mode = False
                self._search_daemon.search_pattern = u''
                self.max_page_index = 0
                self.variables_groups = None
                self._screen_init()

        @staticmethod
        def _create_search_patterns():
            _json_fn = u'Translator3000OtherFiles/variables_patterns.json'
            with utils.renpy_open(_json_fn) as _font_file:
                data = utils.read_json_from_file(_font_file, compressed=False, _is_fo=True)
            patterns = builtins.dict()
            for ptr in data:
                patterns[ptr[0]] = re.compile(u'(?<![a-z])({0})(?![a-z])'.format(u'|'.join(ptr)), flags=re.IGNORECASE | re.UNICODE)
            VarsChanger.SEARCH_PATTERNS = patterns

        @staticmethod
        def _get_value(name, start_from=None):
            if start_from is None:
                start_from = store
            parts = tuple(name.split(u'.'))
            parts, _field = parts[:-1], parts[-1]
            main_object = start_from
            for part in parts:
                main_object = getattr(main_object, part)
            current_value = getattr(main_object, _field)
            return (main_object, _field, current_value)

        @classmethod
        def _set_value(cls, name, value, start_from=None):
            main_object, _field, _i = cls._get_value(name, start_from)
            setattr(main_object, _field, value)

        @classmethod
        def _get_main_variables(cls):
            for store_name, store_dict in renpy.python.store_dicts.items():
                store_name_parts = store_name.split(u'.')
                if store_name_parts[0] == u'store':
                    store_name_parts = store_name_parts[1:]
                check_store_name = u'.'.join(store_name_parts)
                if check_store_name.startswith(u'_'):
                    continue
                if check_store_name in _RENPY_RESERVED_CONSTS:
                    continue
                if u'translator3000' in check_store_name.lower():
                    continue
                for name in store_dict.keys():
                    if name.startswith(u'_'):
                        continue
                    if name in _RENPY_RESERVED_CONSTS:
                        continue
                    if name not in store_dict:
                        continue
                    full_name = u'.'.join((store_name, name))
                    if u'translator3000' in full_name.lower():
                        continue
                    yield full_name, store_name, name

        @classmethod
        def _repr_value(cls, value, _need_repr=True, limit_add=0):
            if _need_repr:
                value = repr(value)
            if isinstance(value, bytes):
                value = value.decode(u'utf_8', u'replace')
            LIMIT = cls._STRING_REPR_LIMIT + limit_add
            assert LIMIT >= 9
            if len(value) >= LIMIT:
                new_size = LIMIT - 8
                part1_size = new_size // 2
                part2_size = new_size - part1_size
                part1 = value[:part1_size].strip()
                part2 = value[-part2_size:].strip()
                value = u'{0}... ...{1}'.format(part1, part2)
            value = value.replace(u'{', u'{{')
            value = value.replace(u'[', u'[[')
            return value

        @classmethod
        def _format_name(cls, name, limit_add=0):
            if not isinstance(name, basestring):
                return cls._repr_value(name, True, limit_add)
            parts = name.split(u'.')
            if not parts:
                return cls._repr_value(name, False, limit_add)
            if parts[0] == u'store':
                parts = parts[1:]
            return cls._repr_value(u'.'.join(parts), False, limit_add)

        def get_vars_for_search(self):
            with self._set_lock:
                return self._get_vars_from_wrapper(self._current_wrapper)

        @classmethod
        def _get_vars_from_wrapper(cls, wrapper=None):
            with VarsChanger.VARIABLES_LOCK:
                if wrapper is None and VarsChanger.ROOT_INSTANCES_CACHE is not None:
                    return VarsChanger.ROOT_INSTANCES_CACHE
                if wrapper:
                    try:
                        variables = tuple(filter(lambda w: w._is_showed_value(), wrapper.get_children()))
                    except Exception:
                        variables = ()
                else:

                    def _check_var(var_wrapper_ob):
                        name = var_wrapper_ob.last_name_part
                        for pattern in cls.SEARCH_PATTERNS.values():
                            if pattern.search(name):
                                return True
                        return False
                    _ex = Exception(u'Undefined error')
                    for _attempt in range(1, 50):
                        cls.LOGGER.debug(u'Get main variables. Attempt %d', _attempt)
                        try:
                            _variables = tuple(cls._get_main_variables())
                            variables = builtins.list()
                            _variables_error_counter = 0
                            for full_name, store_name, name in _variables:
                                try:
                                    main_object, _field_name, _i = cls._get_value(full_name)
                                    val = VarWrapper(main_object, _field_name, var_name=full_name, store_data=(store_name, name))
                                    if not val._is_showed_value():
                                        continue
                                except Exception as ex:
                                    _ex = ex
                                    if _variables_error_counter > 10:
                                        raise
                                    continue
                                variables.append(val)
                            for variable_wr in variables[:]:
                                for child_var_wr in variable_wr.walk(cls.DEEP_OF_SCAN):
                                    if _check_var(child_var_wr):
                                        variables.append(child_var_wr)
                            variables = tuple(variables)
                        except Exception as ex:
                            cls.LOGGER.exception(ex)
                            _ex = ex
                            time.sleep(_attempt * 0.1)
                            continue
                        cls.LOGGER.debug(u'Success')
                        break
                    else:
                        raise _ex
                if not variables:
                    return ()
                result = builtins.dict()
                for variable in variables:
                    key = None
                    name = variable.last_name_part
                    for key_candidate, pattern in cls.SEARCH_PATTERNS.items():
                        if pattern.search(name):
                            key = key_candidate
                            break
                    if key not in result:
                        result[key] = builtins.list()
                    result[key].append(variable)
                other_vars = result.pop(None, None)
                result = tuple(sorted(map(lambda v: (v[0], tuple(v[1])), result.items()), key=lambda x: x[0]))
                if other_vars is not None:
                    result += (None, tuple(other_vars)),
                if wrapper is None:
                    VarsChanger.ROOT_INSTANCES_CACHE = result
                return result

        def get_vars_from_wrapper(self, wrapper=None, current_page=0, get_all=False):
            with VarsChanger.VARIABLES_LOCK:
                return self.sorted_and_crop(self._get_vars_from_wrapper(wrapper), current_page=current_page, add_favorite_group=True, get_all=get_all)

        def sorted_and_crop(self, group_tuple, current_page=0, add_favorite_group=True, get_all=False):
            favorite_vars = builtins.list()
            _result = builtins.list()
            variables_number = 0
            for key, values in group_tuple:
                variables_number += len(values)
                new_values = builtins.list()
                for var_wrapper_ob in values:
                    if add_favorite_group and var_wrapper_ob.favorite:
                        favorite_vars.append(var_wrapper_ob)
                    else:
                        new_values.append(var_wrapper_ob)
                if new_values:
                    _result.append((key, new_values))
            if variables_number < 1:
                return (0, ())
            if favorite_vars:
                _result.insert(0, (self._translator_object._gui.translate(u'\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435', not_translate_mark=False), favorite_vars))

            def _sort_key(var_wrapper_ob):
                _changed_prio = 1
                if var_wrapper_ob.is_ever_been_changed():
                    _changed_prio = 0
                fn = var_wrapper_ob.get_file_definition()
                if not fn:
                    fn = unichr(sys.maxunicode)
                name = self._format_name(var_wrapper_ob.var_name, 1e999)
                return (_changed_prio, fn, name)
            result = builtins.list()
            current_index = None
            _from = current_page * self._ELEMENTS_OF_PAGE_LIMIT
            _to = _from + self._ELEMENTS_OF_PAGE_LIMIT
            for key, values in _result:
                if get_all:
                    new_values = builtins.list(sorted(values, key=_sort_key))
                else:
                    if current_index is not None and current_index >= _to:
                        break
                    new_values = builtins.list()
                    for value in sorted(values, key=_sort_key):
                        if current_index is None:
                            current_index = 0
                        else:
                            current_index += 1
                        if current_index < _from:
                            continue
                        if current_index >= _to:
                            break
                        new_values.append(value)
                if new_values:
                    result.append((key, tuple(new_values)))
            max_page_index = (variables_number - 1) // self._ELEMENTS_OF_PAGE_LIMIT
            return (max_page_index, tuple(result))

        @classmethod
        def _get_value_from_step(cls, _minus=False, _repr=False, _type_detector=None):
            multipler = 1.0
            if _minus:
                multipler *= -1.0
            val = 2.0 ** float(cls.INCREMENT_STEP_POW)
            if val.is_integer():
                val = int(val)
                multipler = int(multipler)
            val *= multipler
            if _type_detector is not None:
                if _type_detector == u'imag':
                    val = complex(imag=val)
                elif _type_detector == u'real':
                    val = complex(real=val)
                elif callable(_type_detector):
                    val = _type_detector(val)
                else:
                    _type_detector = type(_type_detector)
                    val = _type_detector(val)
            if _repr:
                val = cls._repr_value(val)
            return val


    class _SameWrapper(store.NoRollback):
        pass
    if persistent.tr3000_favorite_variables is None:
        persistent.tr3000_favorite_variables = frozenset()






















































init 3:
    screen translator3000_change_variables:
        predict False tag translator3000_screen

        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        on "show" action Function(translator3000.vars_changer._screen_init)
        use translator3000_base_vbox_in_window:
            if translator3000.vars_changer._current_wrapper is not None:
                null height _translator3000_gui.resize_from_1080(20, 0)
                vbox:
                    for name, wrapper in translator3000.vars_changer._current_wrapper.get_name_parts(True):
                        hbox:
                            if wrapper is not None:
                                text "{#notTranslate}=>"
                            textbutton "{{#notTranslate}}{0}".format(translator3000.vars_changer._format_name(name, 3)):
                                text_size _translator3000_gui.resize_from_1080(37, 1)
                                if translator3000.vars_changer.is_active():
                                    action Function(translator3000.vars_changer.set_wrapper, wrapper)
                use translator3000_change_one_varaible_window(translator3000.vars_changer._current_wrapper, False)
                null height _translator3000_gui.resize_from_1080(40, 0)
            window:
                $ _txt = translator3000.vars_changer._repr_value(translator3000.vars_changer._search_daemon.search_pattern, False)
                if translator3000.vars_changer.current_input_id == _translator3000.SearchDaemon.INPUT_ID:
                    vbox:
                        hbox:
                            input value FieldInputValue(translator3000.vars_changer._search_daemon, "search_pattern")
                            if _txt:
                                imagebutton:
                                    yalign .5
                                    idle _translator3000_gui.theme.searchClear
                                    hover _translator3000_gui.theme.searchClearHover
                                    action SetField(translator3000.vars_changer._search_daemon, "search_pattern", "")
                        textbutton translator3000._gui.translate("Прекратить поиск."):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(translator3000.vars_changer, "current_input_id", None)
                elif _txt:
                    hbox:
                        textbutton "{{#notTranslate}}{0}".format(_txt):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(translator3000.vars_changer, "current_input_id", _translator3000.SearchDaemon.INPUT_ID)
                        imagebutton:
                            idle _translator3000_gui.theme.searchClear
                            hover _translator3000_gui.theme.searchClearHover
                            action SetField(translator3000.vars_changer._search_daemon, "search_pattern", "")
                else:
                    textbutton translator3000._gui.translate("Поиск."):
                        text_size _translator3000_gui.resize_from_1080(32, 1)
                        action SetField(translator3000.vars_changer, "current_input_id", _translator3000.SearchDaemon.INPUT_ID)
            null height _translator3000_gui.resize_from_1080(50, 0)
            if translator3000.vars_changer.variables_groups is None:
                label translator3000._gui.translate("Ожидайте..."):
                    text_size _translator3000_gui.resize_from_1080(37, 1)
            elif not translator3000.vars_changer.variables_groups:
                label translator3000._gui.translate("Не найдено"):
                    text_size _translator3000_gui.resize_from_1080(37, 1)
            else:
                window:
                    has vbox
                    label translator3000._gui.translate("\"Шаг\" изменения значений"):
                        text_size _translator3000_gui.resize_from_1080(37, 1)
                    label "{{#notTranslate}}{0}".format(translator3000.vars_changer._get_value_from_step(_repr=True)):
                        text_italic True
                        text_size _translator3000_gui.resize_from_1080(37, 1)
                    null height _translator3000_gui.resize_from_1080(20, 0)
                    hbox:
                        textbutton "{#notTranslate}-":
                            action SetField(_translator3000.VarsChanger, "INCREMENT_STEP_POW", (_translator3000.VarsChanger.INCREMENT_STEP_POW - 1))
                        textbutton "{#notTranslate}+":
                            action SetField(_translator3000.VarsChanger, "INCREMENT_STEP_POW", (_translator3000.VarsChanger.INCREMENT_STEP_POW + 1))
                    if _translator3000.VarsChanger.INCREMENT_STEP_POW:
                        textbutton translator3000._gui.translate("Сбросить."):
                            action SetField(_translator3000.VarsChanger, "INCREMENT_STEP_POW", 0)
                null height _translator3000_gui.resize_from_1080(20, 0)
                vbox:
                    spacing _translator3000_gui.resize_from_1080(15, 0)
                    for group_name, variables_group in translator3000.vars_changer.visible_groups_for_screen:
                        window:
                            has vbox
                            if group_name is not None:
                                label "{{#notTranslate}}{0}".format(group_name):
                                    text_size _translator3000_gui.resize_from_1080(37, 1)
                            for var_wrapper in variables_group:
                                use translator3000_change_one_varaible_window(var_wrapper, True)
                if translator3000.vars_changer.max_page_index > 0:
                    null height _translator3000_gui.resize_from_1080(50, 0)
                    python:
                        pages_on_screen = 5
                        _range_start = max((translator3000.vars_changer._current_page - (pages_on_screen // 2)), 0)
                        _range_stop = min((_range_start + pages_on_screen), (translator3000.vars_changer.max_page_index + 1))
                        _range_start -= (pages_on_screen - (_range_stop - _range_start))
                        _range_start = max(_range_start, 0)
                    window:
                        has vbox
                        hbox:
                            label translator3000._gui.translate("Текущая страница"):
                                text_size _translator3000_gui.resize_from_1080(37, 1)
                            label "{{#notTranslate}}{0}".format(translator3000.vars_changer._repr_value((translator3000.vars_changer._current_page + 1))):
                                text_size _translator3000_gui.resize_from_1080(37, 1)
                        null height _translator3000_gui.resize_from_1080(20, 0)
                        hbox:
                            if translator3000.vars_changer._current_page > 0:
                                textbutton "{#notTranslate}<<":
                                    if translator3000.vars_changer.is_active():
                                        action Function(translator3000.vars_changer.set_page, 0)
                                textbutton "{#notTranslate}<":
                                    if translator3000.vars_changer.is_active():
                                        action Function(translator3000.vars_changer.set_page, (translator3000.vars_changer._current_page - 1))
                            else:
                                text "{#notTranslate} "
                                text "{#notTranslate} "
                            for page_num in range(_range_start, _range_stop):
                                textbutton "{{#notTranslate}}{0}".format(translator3000.vars_changer._repr_value((page_num + 1))):
                                    if page_num != translator3000.vars_changer._current_page:
                                        if translator3000.vars_changer.is_active():
                                            action Function(translator3000.vars_changer.set_page, page_num)
                            if translator3000.vars_changer._current_page < translator3000.vars_changer.max_page_index:
                                textbutton "{#notTranslate}>":
                                    if translator3000.vars_changer.is_active():
                                        action Function(translator3000.vars_changer.set_page, (translator3000.vars_changer._current_page + 1))
                                textbutton "{#notTranslate}>>":
                                    if translator3000.vars_changer.is_active():
                                        action Function(translator3000.vars_changer.set_page, translator3000.vars_changer.max_page_index)
                            else:
                                text "{#notTranslate} "
                                text "{#notTranslate} "
    screen translator3000_change_one_varaible_window(var_wrapper, show_change_attr_block=True):
        predict False tag translator3000_screen

        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        python:
            val = var_wrapper.value
            showing_name = (var_wrapper.var_name if (translator3000.vars_changer._current_wrapper is None) else var_wrapper.last_name_part)
            fn = var_wrapper.get_file_definition()
            _input_id = var_wrapper.var_name
        window:
            has vbox
            xfill True
            window:
                has vbox
                spacing _translator3000_gui.resize_from_1080(10, 0)
                if var_wrapper.is_property():
                    text "{#notTranslate}@property"
                hbox:
                    label "{{#notTranslate}}{0}".format(translator3000.vars_changer._format_name(showing_name)):
                        text_size _translator3000_gui.resize_from_1080(37, 1)
                    imagebutton:
                        idle _translator3000_gui.theme.searchFavorite
                        hover _translator3000_gui.theme.searchFavoriteHover
                        selected_idle _translator3000_gui.theme.searchFavoriteSelected
                        selected_hover _translator3000_gui.theme.searchFavoriteSelectedHover
                        action ToggleField(var_wrapper, "favorite")
                hbox:
                    text "{#notTranslate}="
                    label "{{#notTranslate}}{0}".format(translator3000.vars_changer._repr_value(val)):
                        text_italic True
                        text_size _translator3000_gui.resize_from_1080(35, 1)
                if fn:
                    text "{{#notTranslate}}{0}".format(translator3000.vars_changer._repr_value(fn, False))
            if not var_wrapper.is_changeable():
                text translator3000._gui.translate("Неизменяемое.")
            elif isinstance(val, bool):
                textbutton translator3000._gui.translate("Инвертировать значение."):
                    text_size _translator3000_gui.resize_from_1080(32, 1)
                    action ToggleField(var_wrapper, "value")
            elif isinstance(val, (int, _translator3000.long, float)):
                hbox:
                    textbutton "{{#notTranslate}}{0}".format(translator3000.vars_changer._get_value_from_step(_minus=True, _repr=True, _type_detector=val)):
                        text_size _translator3000_gui.resize_from_1080(32, 1)
                        action SetField(var_wrapper, "value", (val - translator3000.vars_changer._get_value_from_step(_type_detector=val)))
                    textbutton "+{0}".format(translator3000.vars_changer._get_value_from_step(_repr=True, _type_detector=val)):
                        text_size _translator3000_gui.resize_from_1080(32, 1)
                        action SetField(var_wrapper, "value", (val + translator3000.vars_changer._get_value_from_step(_type_detector=val)))
            elif isinstance(val, complex):
                vbox:
                    hbox:
                        textbutton "{{#notTranslate}}{0}".format(translator3000.vars_changer._get_value_from_step(_minus=True, _repr=True)):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(var_wrapper, "value", (val - translator3000.vars_changer._get_value_from_step(_type_detector="real")))
                        textbutton "+{0}".format(translator3000.vars_changer._get_value_from_step(_repr=True)):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(var_wrapper, "value", (val + translator3000.vars_changer._get_value_from_step(_type_detector="real")))
                    hbox:
                        textbutton "{{#notTranslate}}{0}".format(translator3000.vars_changer._get_value_from_step(_minus=True, _repr=True, _type_detector="imag")):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(var_wrapper, "value", (val - translator3000.vars_changer._get_value_from_step(_type_detector="imag")))
                        textbutton "+{0}".format(translator3000.vars_changer._get_value_from_step(_repr=True, _type_detector="imag")):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(var_wrapper, "value", (val + translator3000.vars_changer._get_value_from_step(_type_detector="imag")))
            elif isinstance(val, _translator3000.unicode):
                if translator3000.vars_changer.current_input_id == _input_id:
                    vbox:
                        input value FieldInputValue(var_wrapper, "value")
                        textbutton translator3000._gui.translate("Подтвердить изменения."):
                            text_size _translator3000_gui.resize_from_1080(32, 1)
                            action SetField(translator3000.vars_changer, "current_input_id", None)
                else:
                    $ _txt = translator3000.vars_changer._repr_value(val, False)
                    textbutton ("{{#notTranslate}}{0}".format(_txt) if _txt else translator3000._gui.translate("Редактировать текст.")):
                        text_size _translator3000_gui.resize_from_1080(32, 1)
                        action SetField(translator3000.vars_changer, "current_input_id", _input_id)
            if show_change_attr_block:
                textbutton translator3000._gui.translate("Изменить свойства объекта (если имеются)."):
                    text_size _translator3000_gui.resize_from_1080(32, 1)
                    if translator3000.vars_changer.is_active():
                        action Function(translator3000.vars_changer.set_wrapper, var_wrapper)

