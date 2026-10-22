"""CustomTkinter application shell: window, sidebar, screens, status bar, dialogs.

The shell owns the Tk main loop and marshalling: network/session work runs through
:class:`~market_monitor_gui.background.task_runner.TaskRunner`, whose callbacks are
delivered by :meth:`Shell._poll` on the main thread. Widgets never touch http,
cookies, or secrets directly.
"""

from __future__ import annotations

import tkinter as tk
from contextlib import suppress
from datetime import UTC, datetime

import customtkinter as ctk

from market_monitor_gui.api.client import ApiClient
from market_monitor_gui.api.dto import FilterResponse, GroupResponse, LiveResponse, SettingsResponse
from market_monitor_gui.api.errors import ApiError, ErrorKind
from market_monitor_gui.app import AppContext
from market_monitor_gui.auth.session import SessionManager, SessionState
from market_monitor_gui.services.connection import forget_secret, save_connection, store_secret
from market_monitor_gui.services.errors import text_key_for_exception
from market_monitor_gui.services.filters import (
    FiltersData,
    create_filter,
    delete_filter,
    load_filters,
)
from market_monitor_gui.services.groups import (
    GroupsData,
    create_group,
    delete_group,
    load_groups,
    set_group_enabled,
    update_group,
)
from market_monitor_gui.services.overview import OverviewData, load_overview
from market_monitor_gui.services.settings import SettingsData, load_settings, save_settings
from market_monitor_gui.texts import ru
from market_monitor_gui.ui import icons, theme
from market_monitor_gui.ui.connection_state import ConnectionState, state_for_error
from market_monitor_gui.ui.dialogs.about import AboutDialog
from market_monitor_gui.ui.dialogs.base import BaseDialog
from market_monitor_gui.ui.dialogs.confirm_delete import ConfirmDeleteDialog
from market_monitor_gui.ui.dialogs.connection import ConnectionDialog
from market_monitor_gui.ui.dialogs.filter_editor import FilterEditorDialog
from market_monitor_gui.ui.dialogs.group_editor import GroupEditorDialog
from market_monitor_gui.ui.dialogs.login import LoginDialog
from market_monitor_gui.ui.forms import (
    ConnectionFormValues,
    FilterFormValues,
    GroupFormValues,
    LoginFormValues,
    login_error_text,
)
from market_monitor_gui.ui.links import open_external_url
from market_monitor_gui.ui.menu import AppMenu, MenuAction
from market_monitor_gui.ui.navigation import SCREEN_ORDER, Screen, screen_from_value
from market_monitor_gui.ui.screens.auth import AuthScreen
from market_monitor_gui.ui.screens.base import ScreenFrame
from market_monitor_gui.ui.screens.filters import FiltersScreen
from market_monitor_gui.ui.screens.groups import GroupsScreen
from market_monitor_gui.ui.screens.help import HelpScreen
from market_monitor_gui.ui.screens.overview import OverviewScreen
from market_monitor_gui.ui.screens.settings import SettingsScreen
from market_monitor_gui.ui.sidebar import Sidebar
from market_monitor_gui.ui.status_bar import MESSAGE_TTL_MS, MessageKind, StatusBar

POLL_INTERVAL_MS = 50


class Shell(ctk.CTk):
    """The single application window and its wiring."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._ctx = context
        self._fonts = theme.build_fonts()
        self._screens: dict[Screen, ScreenFrame] = {}
        self._current_frame: ScreenFrame | None = None
        self._current_screen: Screen | None = None
        self._login_dialog: LoginDialog | None = None
        self._connection_dialog: ConnectionDialog | None = None
        self._group_editor: GroupEditorDialog | None = None
        self._confirm_delete: ConfirmDeleteDialog | None = None
        self._filter_editor: FilterEditorDialog | None = None
        self._relogin_prompt_shown = False
        self._poll_job: str | None = None
        self._message_job: str | None = None
        self._status = ConnectionState.OFFLINE

        self._session = SessionManager(
            context.api,
            secret_provider=context.resolver.resolve,
            on_state_change=self._on_session_state,
        )

        self._configure_window()
        self._build_layout()
        self._build_screens()
        self._menu = AppMenu(self._sidebar.footer(), fonts=self._fonts, on_action=self._on_menu)
        self._bind_shortcuts()

    # -- construction ---------------------------------------------------------

    def _configure_window(self) -> None:
        self.title(ru.APP_NAME)
        self._icon_applied = icons.apply_window_icon(self)
        self.minsize(theme.MIN_WIDTH, theme.MIN_HEIGHT)
        geometry = self._ctx.ui_state.get_window_geometry()
        self.geometry(geometry or f"{theme.MIN_WIDTH}x{theme.MIN_HEIGHT}")
        theme.apply_appearance(self._ctx.ui_state.get_theme())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=theme.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self._sidebar = Sidebar(self, fonts=self._fonts, on_select=self._select_screen)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._content = ctk.CTkFrame(self, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self._status_bar = StatusBar(self, fonts=self._fonts)
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _build_screens(self) -> None:
        self._auth_screen = AuthScreen(
            self._content, fonts=self._fonts, on_login=self._request_login
        )
        self._overview = OverviewScreen(
            self._content,
            fonts=self._fonts,
            on_refresh=self._refresh_overview,
            on_check=self._check_connection,
        )
        self._groups_screen = GroupsScreen(
            self._content,
            fonts=self._fonts,
            on_refresh=self._refresh_groups,
            on_add=self._open_group_editor_add,
            on_edit=self._open_group_editor_edit,
            on_toggle=self._toggle_group,
            on_delete=self._confirm_delete_group,
            on_open_url=self._open_external_url,
        )
        self._settings_screen = SettingsScreen(
            self._content,
            fonts=self._fonts,
            on_refresh=self._refresh_settings,
            on_save=self._save_settings,
        )
        self._filters_screen = FiltersScreen(
            self._content,
            fonts=self._fonts,
            on_refresh=self._refresh_filters,
            on_add=self._open_filter_editor,
            on_delete=self._confirm_delete_filter,
        )
        self._help_screen = HelpScreen(self._content, fonts=self._fonts)
        self._screens = {
            Screen.OVERVIEW: self._overview,
            Screen.GROUPS: self._groups_screen,
            Screen.SETTINGS: self._settings_screen,
            Screen.FILTERS: self._filters_screen,
            Screen.HELP: self._help_screen,
        }
        for frame in (self._auth_screen, *self._screens.values()):
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def _bind_shortcuts(self) -> None:
        for index, screen in enumerate(SCREEN_ORDER, start=1):
            self.bind(
                f"<Control-Key-{index}>",
                lambda _event, selected=screen: self._select_screen(selected),
            )
        self.bind("<F5>", lambda _event: self._refresh_current())

    # -- startup --------------------------------------------------------------

    def start(self) -> None:
        """Show the auth flow and begin polling the task runner."""
        self._start_polling()
        self._show_auth()
        secret = self._ctx.resolver.resolve()
        if secret:
            self._begin_login(secret, dialog=None)
        else:
            self._set_status(ConnectionState.OFFLINE)
            self._open_login_dialog()

    def _start_polling(self) -> None:
        self._poll_job = self.after(POLL_INTERVAL_MS, self._poll)

    def _poll(self) -> None:
        # Reschedule first so draining (which may open a modal dialog) keeps polling.
        self._poll_job = self.after(POLL_INTERVAL_MS, self._poll)
        self._ctx.runner.drain()

    # -- navigation -----------------------------------------------------------

    def _select_screen(self, screen: Screen) -> None:
        if self._session.state is not SessionState.SIGNED_IN:
            return
        self._show_screen(screen)

    def _show_screen(self, screen: Screen) -> None:
        frame = self._screens.get(screen)
        if frame is None:
            return
        self._sidebar.set_active(screen)
        self._current_screen = screen
        self._swap_frame(frame)
        self._ctx.ui_state.set_last_screen(screen.value)
        if screen is Screen.OVERVIEW:
            self._refresh_overview()
        elif screen is Screen.GROUPS:
            self._refresh_groups()
        elif screen is Screen.SETTINGS:
            self._refresh_settings()
        elif screen is Screen.FILTERS:
            self._refresh_filters()

    def _refresh_current(self) -> None:
        if self._current_screen is Screen.OVERVIEW:
            self._refresh_overview()
        elif self._current_screen is Screen.GROUPS:
            self._refresh_groups()
        elif self._current_screen is Screen.SETTINGS:
            self._refresh_settings()
        elif self._current_screen is Screen.FILTERS:
            self._refresh_filters()

    def _show_auth(self) -> None:
        self._current_screen = None
        self._sidebar.clear_active()
        self._auth_screen.set_login_label(
            ru.ACTION_LOGIN_AGAIN if self._ctx.resolver.has_secret() else ru.ACTION_LOGIN
        )
        self._swap_frame(self._auth_screen)

    def _swap_frame(self, frame: ScreenFrame) -> None:
        if self._current_frame is not None and self._current_frame is not frame:
            self._current_frame.on_hide()
            self._current_frame.grid_remove()
        frame.grid()
        frame.tkraise()
        self._current_frame = frame
        frame.on_show()

    # -- session --------------------------------------------------------------

    def _on_session_state(self, state: SessionState) -> None:
        # Called on whatever thread changed the session; marshal to the main thread.
        self._ctx.runner.post(lambda: self._handle_session_state(state))

    def _handle_session_state(self, state: SessionState) -> None:
        if state is SessionState.SIGNED_IN:
            self._relogin_prompt_shown = False
            self._close_login_dialog()
            self._sidebar.set_enabled(True)
            self._set_status(ConnectionState.CONNECTED)
            if self._current_screen is None:
                self._show_screen(screen_from_value(self._ctx.ui_state.get_last_screen()))
        elif state is SessionState.EXPIRED:
            self._sidebar.set_enabled(False)
            self._set_status(ConnectionState.SESSION_EXPIRED)
            self._show_auth()
            self._open_login_dialog_once()
        else:
            self._sidebar.set_enabled(False)
            self._show_auth()

    def _begin_login(
        self,
        secret: str,
        *,
        dialog: LoginDialog | None,
        remember: bool = False,
    ) -> None:
        self._set_status(ConnectionState.CONNECTING)
        if dialog is not None:
            dialog.set_busy(True)
        handle = self._ctx.runner.submit(
            lambda: self._session.login(secret),
            on_ok=lambda state: self._login_succeeded(state, secret=secret, remember=remember),
            on_err=lambda exc: self._login_failed(exc, dialog=dialog),
            key="login",
        )
        if handle is None and dialog is not None:
            dialog.set_busy(False)

    def _login_succeeded(self, _state: SessionState, *, secret: str, remember: bool) -> None:
        if remember:
            outcome = store_secret(self._ctx.secrets, secret)
            if not outcome.ok:
                self._flash_message(
                    ru.text_for(outcome.error_key or "ERR_UNEXPECTED"), MessageKind.ERROR
                )
        self._close_login_dialog()

    def _login_failed(self, exc: BaseException, *, dialog: LoginDialog | None) -> None:
        state = state_for_error(exc)
        if state is None:
            # Network-level failure: keep the current screen and let the operator retry.
            self._set_status(ConnectionState.OFFLINE)
            self._flash_message(ru.text_for(login_error_text(exc)), MessageKind.ERROR)
            if dialog is not None:
                dialog.set_busy(False)
            return
        self._set_status(state)
        target = dialog if dialog is not None else self._login_dialog
        if target is None or not self._dialog_alive(target):
            target = self._spawn_login_dialog(secret_available=False)
        target.show_error(login_error_text(exc))

    # -- login dialog ---------------------------------------------------------

    def _spawn_login_dialog(self, *, secret_available: bool) -> LoginDialog:
        dialog = LoginDialog(
            self,
            fonts=self._fonts,
            secret_available=secret_available,
            on_submit=lambda values: self._submit_login(dialog, values),
            on_open_connection=self._open_connection_dialog,
        )
        self._login_dialog = dialog
        dialog.show_modal()
        return dialog

    def _submit_login(self, dialog: LoginDialog, values: LoginFormValues) -> None:
        if values.secret is None:
            secret = self._ctx.resolver.resolve()
            if not secret:
                dialog.show_error("ERR_NO_SECRET")
                return
            self._begin_login(secret, dialog=dialog)
            return
        self._begin_login(values.secret, dialog=dialog, remember=values.remember)

    def _open_login_dialog(self) -> None:
        if self._dialog_alive(self._login_dialog):
            return
        self._spawn_login_dialog(secret_available=self._ctx.resolver.has_secret())

    def _request_login(self) -> None:
        """Sign in from the auth screen without re-typing a stored secret."""
        secret = self._ctx.resolver.resolve()
        if secret:
            self._begin_login(secret, dialog=None)
        else:
            self._open_login_dialog()

    def _open_login_dialog_once(self) -> None:
        if self._relogin_prompt_shown:
            return
        self._relogin_prompt_shown = True
        self._open_login_dialog()

    def _close_login_dialog(self) -> None:
        if self._dialog_alive(self._login_dialog):
            assert self._login_dialog is not None
            self._login_dialog.close()

    @staticmethod
    def _dialog_alive(dialog: BaseDialog | None) -> bool:
        return dialog is not None and bool(dialog.winfo_exists())

    # -- connection settings --------------------------------------------------

    def _open_connection_dialog(self) -> None:
        if self._dialog_alive(self._connection_dialog):
            return
        dialog = ConnectionDialog(
            self,
            fonts=self._fonts,
            initial_origin=self._ctx.api.origin,
            secret_saved=self._ctx.resolver.has_stored_secret(),
            env_secret=self._ctx.resolver.has_env_secret(),
            on_save=lambda values: self._save_connection(dialog, values),
            on_check=lambda origin: self._check_connection(origin, dialog=dialog),
            on_forget=lambda: self._confirm_forget_secret(dialog),
        )
        self._connection_dialog = dialog
        dialog.show_modal()

    def _save_connection(self, dialog: ConnectionDialog, values: ConnectionFormValues) -> None:
        changed = values.origin != self._ctx.api.origin
        outcome = save_connection(
            self._ctx.config,
            self._ctx.secrets,
            origin=values.origin,
            secret=values.secret,
            save_secret=values.remember,
            clear_secret=not values.remember,
        )
        if not outcome.ok:
            dialog.show_error(outcome.error_key or "ERR_UNEXPECTED")
            return
        dialog.set_secret_saved(self._ctx.resolver.has_stored_secret())
        dialog.close()
        if changed:
            self._rebuild_api(values.origin)
            self._flash_message(ru.CONN_ORIGIN_CHANGED_RELOGIN, MessageKind.SUCCESS)
        login_secret = values.secret or self._ctx.resolver.resolve()
        if login_secret:
            self._begin_login(login_secret, dialog=None)
        elif self._session.state is SessionState.SIGNED_IN:
            self._flash_message(ru.CONN_SAVED, MessageKind.SUCCESS)
        else:
            self._show_auth()
            self._open_login_dialog()

    def _confirm_forget_secret(self, connection_dialog: ConnectionDialog) -> None:
        confirm = ConfirmDeleteDialog(
            connection_dialog,
            fonts=self._fonts,
            title=ru.CONFIRM_FORGET_SECRET_TITLE,
            question=ru.fmt_confirm_forget_secret(),
            warning=ru.CONFIRM_FORGET_SECRET_WARNING,
            confirm_label=ru.ACTION_FORGET_SECRET,
            on_confirm=lambda: self._forget_secret(connection_dialog, confirm),
        )
        self._confirm_delete = confirm
        confirm.show_modal()

    def _forget_secret(self, connection_dialog: ConnectionDialog, confirm: BaseDialog) -> None:
        outcome = forget_secret(self._ctx.secrets)
        confirm.close()
        if not outcome.ok:
            connection_dialog.show_error(outcome.error_key or "ERR_UNEXPECTED")
            return
        connection_dialog.set_secret_saved(False)
        self._flash_message(ru.MSG_SECRET_FORGOTTEN, MessageKind.SUCCESS)

    def _disconnect(self) -> None:
        self._session.disconnect()
        self._sidebar.set_enabled(False)
        self._set_status(ConnectionState.DISCONNECTED)
        self._show_auth()
        if self._ctx.resolver.has_secret():
            self._flash_message(ru.MSG_DISCONNECTED, MessageKind.SUCCESS)
        else:
            self._flash_message(ru.MSG_DISCONNECTED_NO_SECRET, MessageKind.SUCCESS)

    def _rebuild_api(self, origin: str) -> None:
        previous = self._ctx.api
        self._ctx.api = ApiClient.create(origin)
        self._session = SessionManager(
            self._ctx.api,
            secret_provider=self._ctx.resolver.resolve,
            on_state_change=self._on_session_state,
        )
        previous.close()
        self._relogin_prompt_shown = False
        self._sidebar.set_enabled(False)
        self._show_auth()

    # -- health / overview ----------------------------------------------------

    def _check_connection(
        self, origin: str | None = None, *, dialog: ConnectionDialog | None = None
    ) -> None:
        target = origin or self._ctx.api.origin
        self._set_status(ConnectionState.CONNECTING)

        def probe() -> LiveResponse:
            if target == self._ctx.api.origin:
                return self._ctx.api.live()
            temporary = ApiClient.create(target)
            try:
                return temporary.live()
            finally:
                temporary.close()

        self._ctx.runner.submit(
            probe,
            on_ok=lambda _response: self._check_succeeded(dialog),
            on_err=lambda exc: self._check_failed(exc, dialog),
            key="check",
        )

    def _check_succeeded(self, dialog: ConnectionDialog | None) -> None:
        self._set_status(ConnectionState.CONNECTED)
        if self._dialog_alive(dialog):
            assert dialog is not None
            dialog.show_check_result(True, ru.STATUS_CHECK_OK)
        else:
            self._flash_message(ru.STATUS_CHECK_OK, MessageKind.SUCCESS)

    def _check_failed(self, exc: BaseException, dialog: ConnectionDialog | None) -> None:
        self._set_status(state_for_error(exc) or ConnectionState.OFFLINE)
        text_key = text_key_for_exception(exc)
        if self._dialog_alive(dialog):
            assert dialog is not None
            dialog.show_check_result(False, ru.text_for(text_key))
        else:
            self._flash_message(ru.text_for(text_key), MessageKind.ERROR)

    def _refresh_overview(self) -> None:
        if self._session.state is not SessionState.SIGNED_IN:
            return
        self._overview.set_loading()
        self._set_status(ConnectionState.CONNECTING)
        self._ctx.runner.submit(
            lambda: load_overview(self._session, self._ctx.api, self._ctx.cache),
            on_ok=self._overview_loaded,
            on_err=self._overview_failed,
            key="overview",
        )

    def _overview_loaded(self, data: OverviewData) -> None:
        self._overview.render(data)
        if data.from_cache:
            self._set_status(ConnectionState.OFFLINE)
        else:
            self._set_status(ConnectionState.CONNECTED)
            self._status_bar.set_last_refresh(datetime.now(UTC))

    def _overview_failed(self, exc: BaseException) -> None:
        self._overview.show_read_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    # -- groups ---------------------------------------------------------------

    def _refresh_groups(self) -> None:
        if self._session.state is not SessionState.SIGNED_IN:
            return
        self._groups_screen.set_loading()
        self._set_status(ConnectionState.CONNECTING)
        self._ctx.runner.submit(
            lambda: load_groups(self._session, self._ctx.api, self._ctx.cache),
            on_ok=self._groups_loaded,
            on_err=self._groups_failed,
            key="groups",
        )

    def _groups_loaded(self, data: GroupsData) -> None:
        self._groups_screen.render(data)
        if data.from_cache:
            self._set_status(ConnectionState.OFFLINE)
        else:
            self._set_status(ConnectionState.CONNECTED)
            self._status_bar.set_last_refresh(datetime.now(UTC))

    def _groups_failed(self, exc: BaseException) -> None:
        self._groups_screen.show_read_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    def _open_group_editor_add(self) -> None:
        self._open_group_editor(None)

    def _open_group_editor_edit(self, group: GroupResponse) -> None:
        self._open_group_editor(group)

    def _open_group_editor(self, group: GroupResponse | None) -> None:
        if self._dialog_alive(self._group_editor):
            return
        initial = (
            GroupFormValues(name=group.name, url=group.url, enabled=group.enabled)
            if group is not None
            else None
        )
        dialog = GroupEditorDialog(
            self,
            fonts=self._fonts,
            title=ru.GROUP_EDITOR_TITLE_EDIT if group is not None else ru.GROUP_EDITOR_TITLE_ADD,
            initial=initial,
            on_submit=lambda values: self._save_group(dialog, group, values),
        )
        self._group_editor = dialog
        dialog.show_modal()

    def _save_group(
        self, dialog: GroupEditorDialog, group: GroupResponse | None, values: GroupFormValues
    ) -> None:
        if group is None:
            self._submit_group_create(dialog, values)
        else:
            self._submit_group_update(dialog, group.id, values)

    def _submit_group_create(self, dialog: GroupEditorDialog, values: GroupFormValues) -> None:
        self._ctx.runner.submit(
            lambda: create_group(
                self._session,
                self._ctx.api,
                name=values.name,
                url=values.url,
                enabled=values.enabled,
            ),
            on_ok=lambda _result: self._group_saved(dialog),
            on_err=lambda exc: self._group_write_failed(dialog, exc),
            key="group-create",
        )

    def _submit_group_update(
        self, dialog: GroupEditorDialog, group_id: int, values: GroupFormValues
    ) -> None:
        self._ctx.runner.submit(
            lambda: update_group(
                self._session,
                self._ctx.api,
                group_id,
                name=values.name,
                url=values.url,
                enabled=values.enabled,
            ),
            on_ok=lambda _result: self._group_saved(dialog),
            on_err=lambda exc: self._group_write_failed(dialog, exc),
            key=f"group-update-{group_id}",
        )

    def _group_saved(self, dialog: GroupEditorDialog) -> None:
        dialog.close()
        self._flash_message(ru.GROUPS_SAVED, MessageKind.SUCCESS)
        self._refresh_groups()

    def _group_write_failed(self, dialog: GroupEditorDialog, exc: BaseException) -> None:
        dialog.show_error(text_key_for_exception(exc))

    def _toggle_group(self, group: GroupResponse) -> None:
        target = not group.enabled
        self._groups_screen.set_row_busy(group.id, True)
        self._ctx.runner.submit(
            lambda: set_group_enabled(self._session, self._ctx.api, group.id, enabled=target),
            on_ok=self._group_toggled,
            on_err=lambda exc: self._group_mutation_failed(group.id, exc),
            key=f"group-toggle-{group.id}",
        )

    def _group_toggled(self, updated: GroupResponse) -> None:
        self._groups_screen.set_row_busy(updated.id, False)
        self._refresh_groups()

    def _group_mutation_failed(self, group_id: int, exc: BaseException) -> None:
        self._groups_screen.set_row_busy(group_id, False)
        self._groups_screen.show_write_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    def _confirm_delete_group(self, group: GroupResponse) -> None:
        if self._dialog_alive(self._confirm_delete):
            return
        dialog = ConfirmDeleteDialog(
            self,
            fonts=self._fonts,
            question=ru.fmt_confirm_delete_group(group.name),
            confirm_label=ru.ACTION_DELETE,
            on_confirm=lambda: self._perform_delete(dialog, group),
        )
        self._confirm_delete = dialog
        dialog.show_modal()

    def _perform_delete(self, dialog: ConfirmDeleteDialog, group: GroupResponse) -> None:
        self._groups_screen.set_row_busy(group.id, True)
        self._ctx.runner.submit(
            lambda: delete_group(self._session, self._ctx.api, group.id),
            on_ok=lambda _result: self._group_deleted(dialog, group),
            on_err=lambda exc: self._group_delete_failed(dialog, group, exc),
            key=f"group-delete-{group.id}",
        )

    def _group_deleted(self, dialog: ConfirmDeleteDialog, group: GroupResponse) -> None:
        dialog.close()
        self._groups_screen.set_row_busy(group.id, False)
        self._flash_message(ru.GROUPS_DELETED, MessageKind.SUCCESS)
        self._refresh_groups()

    def _group_delete_failed(
        self, dialog: ConfirmDeleteDialog, group: GroupResponse, exc: BaseException
    ) -> None:
        self._groups_screen.set_row_busy(group.id, False)
        if isinstance(exc, ApiError) and exc.kind is ErrorKind.CONFLICT:
            if self._dialog_alive(dialog):
                dialog.show_conflict(
                    "ERR_CONFLICT_GROUP_IN_USE",
                    ru.ACTION_DISABLE_GROUP,
                    lambda: self._disable_from_conflict(dialog, group),
                )
            else:
                self._groups_screen.show_conflict(group.id)
            return
        if self._dialog_alive(dialog):
            dialog.show_error(text_key_for_exception(exc))
        else:
            self._groups_screen.show_write_error(text_key_for_exception(exc))

    def _disable_from_conflict(self, dialog: ConfirmDeleteDialog, group: GroupResponse) -> None:
        dialog.close()
        self._disable_group(group)

    def _disable_group(self, group: GroupResponse) -> None:
        """Disable a group explicitly (never a toggle) after a delete conflict."""
        self._groups_screen.set_row_busy(group.id, True)
        self._ctx.runner.submit(
            lambda: set_group_enabled(self._session, self._ctx.api, group.id, enabled=False),
            on_ok=self._group_disabled,
            on_err=lambda exc: self._group_mutation_failed(group.id, exc),
            key=f"group-disable-{group.id}",
        )

    def _group_disabled(self, updated: GroupResponse) -> None:
        self._groups_screen.set_row_busy(updated.id, False)
        self._flash_message(ru.GROUP_DISABLED, MessageKind.SUCCESS)
        self._refresh_groups()

    def _open_external_url(self, url: str) -> None:
        """Open any external URL (group or repository) without blocking the UI thread."""
        self._ctx.runner.submit(
            lambda: open_external_url(url),
            on_ok=self._url_opened,
            on_err=lambda _exc: self._flash_message(ru.ERR_OPEN_LINK, MessageKind.ERROR),
            key="open-external-url",
        )

    def _url_opened(self, opened: bool) -> None:
        if not opened:
            self._flash_message(ru.ERR_OPEN_LINK, MessageKind.ERROR)

    # -- settings -------------------------------------------------------------

    def _refresh_settings(self) -> None:
        if self._session.state is not SessionState.SIGNED_IN:
            return
        self._settings_screen.set_loading()
        self._set_status(ConnectionState.CONNECTING)
        self._ctx.runner.submit(
            lambda: load_settings(self._session, self._ctx.api, self._ctx.cache),
            on_ok=self._settings_loaded,
            on_err=self._settings_failed,
            key="settings",
        )

    def _settings_loaded(self, data: SettingsData) -> None:
        self._settings_screen.render(data)
        if data.from_cache:
            self._set_status(ConnectionState.OFFLINE)
        else:
            self._set_status(ConnectionState.CONNECTED)
            self._status_bar.set_last_refresh(datetime.now(UTC))

    def _settings_failed(self, exc: BaseException) -> None:
        self._settings_screen.show_read_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    def _save_settings(self, value: float) -> None:
        self._ctx.runner.submit(
            lambda: save_settings(
                self._session,
                self._ctx.api,
                self._ctx.cache,
                price_drop_threshold_percent=value,
            ),
            on_ok=self._settings_saved,
            on_err=self._settings_save_failed,
            key="settings-save",
        )

    def _settings_saved(self, response: SettingsResponse) -> None:
        self._settings_screen.show_saved(response.price_drop_threshold_percent)
        self._flash_message(ru.SETTINGS_SAVED, MessageKind.SUCCESS)
        self._set_status(ConnectionState.CONNECTED)

    def _settings_save_failed(self, exc: BaseException) -> None:
        self._settings_screen.show_write_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    # -- filters (exclusions) -------------------------------------------------

    def _refresh_filters(self) -> None:
        if self._session.state is not SessionState.SIGNED_IN:
            return
        self._filters_screen.set_loading()
        self._set_status(ConnectionState.CONNECTING)
        self._ctx.runner.submit(
            lambda: load_filters(self._session, self._ctx.api, self._ctx.cache),
            on_ok=self._filters_loaded,
            on_err=self._filters_failed,
            key="filters",
        )

    def _filters_loaded(self, data: FiltersData) -> None:
        self._filters_screen.render(data)
        if data.from_cache:
            self._set_status(ConnectionState.OFFLINE)
        else:
            self._set_status(ConnectionState.CONNECTED)
            self._status_bar.set_last_refresh(datetime.now(UTC))

    def _filters_failed(self, exc: BaseException) -> None:
        self._filters_screen.show_read_error(text_key_for_exception(exc))
        self._set_status(state_for_error(exc) or self._status)

    def _open_filter_editor(self) -> None:
        if self._dialog_alive(self._filter_editor):
            return
        dialog = FilterEditorDialog(
            self,
            fonts=self._fonts,
            on_submit=lambda values: self._save_filter(dialog, values),
        )
        self._filter_editor = dialog
        dialog.show_modal()

    def _save_filter(self, dialog: FilterEditorDialog, values: FilterFormValues) -> None:
        self._ctx.runner.submit(
            lambda: create_filter(self._session, self._ctx.api, phrase=values.phrase),
            on_ok=lambda _result: self._filter_saved(dialog),
            on_err=lambda exc: self._filter_write_failed(dialog, exc),
            key="filter-create",
        )

    def _filter_saved(self, dialog: FilterEditorDialog) -> None:
        dialog.close()
        self._flash_message(ru.FILTERS_SAVED, MessageKind.SUCCESS)
        self._refresh_filters()

    def _filter_write_failed(self, dialog: FilterEditorDialog, exc: BaseException) -> None:
        dialog.show_error(text_key_for_exception(exc))

    def _confirm_delete_filter(self, item: FilterResponse) -> None:
        if self._dialog_alive(self._confirm_delete):
            return
        dialog = ConfirmDeleteDialog(
            self,
            fonts=self._fonts,
            title=ru.CONFIRM_DELETE_FILTER_TITLE,
            question=ru.fmt_confirm_delete_filter(item.phrase),
            confirm_label=ru.ACTION_DELETE,
            on_confirm=lambda: self._perform_delete_filter(dialog, item),
        )
        self._confirm_delete = dialog
        dialog.show_modal()

    def _perform_delete_filter(self, dialog: ConfirmDeleteDialog, item: FilterResponse) -> None:
        self._filters_screen.set_row_busy(item.id, True)
        self._ctx.runner.submit(
            lambda: delete_filter(self._session, self._ctx.api, item.id),
            on_ok=lambda _result: self._filter_deleted(dialog, item),
            on_err=lambda exc: self._filter_delete_failed(dialog, item, exc),
            key=f"filter-delete-{item.id}",
        )

    def _filter_deleted(self, dialog: ConfirmDeleteDialog, item: FilterResponse) -> None:
        dialog.close()
        self._filters_screen.set_row_busy(item.id, False)
        self._flash_message(ru.FILTERS_DELETED, MessageKind.SUCCESS)
        self._refresh_filters()

    def _filter_delete_failed(
        self, dialog: ConfirmDeleteDialog, item: FilterResponse, exc: BaseException
    ) -> None:
        self._filters_screen.set_row_busy(item.id, False)
        if self._dialog_alive(dialog):
            dialog.show_error(text_key_for_exception(exc))
        else:
            self._filters_screen.show_write_error(text_key_for_exception(exc))

    # -- menu / status / shutdown ---------------------------------------------

    def _flash_message(self, text: str, kind: MessageKind = MessageKind.INFO) -> None:
        """Set the status-bar message and clear it after the kind's linger time."""
        if self._message_job is not None:
            with suppress(tk.TclError):
                self.after_cancel(self._message_job)
        self._status_bar.set_message(text, kind)
        self._message_job = self.after(MESSAGE_TTL_MS[kind], self._clear_message)

    def _clear_message(self) -> None:
        self._message_job = None
        self._status_bar.set_message(None)

    def _on_menu(self, action: MenuAction) -> None:
        if action is MenuAction.CONNECTION:
            self._open_connection_dialog()
        elif action is MenuAction.CHECK:
            self._check_connection()
        elif action is MenuAction.DISCONNECT:
            self._disconnect()
        elif action is MenuAction.ABOUT:
            AboutDialog(self, fonts=self._fonts, on_open_url=self._open_external_url).show_modal()

    def _set_status(self, state: ConnectionState) -> None:
        self._status = state
        self._status_bar.set_state(state)

    def _on_close(self) -> None:
        if self._poll_job is not None:
            with suppress(tk.TclError):
                self.after_cancel(self._poll_job)
        if self._message_job is not None:
            with suppress(tk.TclError):
                self.after_cancel(self._message_job)
        with suppress(Exception):
            self._ctx.ui_state.set_window_geometry(self.geometry())
        self._ctx.close()
        self.destroy()
