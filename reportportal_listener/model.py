# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Union


class Suite(object):
    """Object describes suite."""

    def __init__(self, attributes: Dict[str, Any]) -> None:
        """Suite initialization.

        Args:
            attributes: suite attributes from Robot Framework.
        """
        super(Suite, self).__init__()
        self.suites: List[str] = attributes["suites"]
        self.doc: str = attributes["doc"]
        self.source: str = attributes["source"]
        self.total_tests: int = attributes["totaltests"]
        self.longname: str = attributes["longname"]
        self.robot_id: str = attributes["id"]
        self.metadata: Dict[str, str] = attributes["metadata"]
        self.start_time: str = attributes["starttime"]
        self.end_time: str = attributes.get("endtime", "")
        self.status: str = attributes.get("status", "")
        self.message: Dict[str, Any] = {}
        self.statistics: str = attributes.get("statistics", "")
        self.rp_item_type: str = "TEST" if attributes.get("tests") else "SUITE"
        self.tests: List[Test] = []
        self.type: str = "SUITE"
        self.setup: Optional[Keyword] = None
        self.teardown: Optional[Keyword] = None

    def update(self, attributes: Dict[str, Any]) -> None:
        """Update suite STATUS, MESSAGE, STATISTICS and ENDTIME.

        Args:
            attributes (dict): suite attributes.
        """
        self.end_time = attributes.get("endtime", "")
        self.status = attributes.get("status", "")
        self.statistics = attributes.get("statistics", "")


class Test(object):
    """Object describes test."""

    def __init__(self, name: str, attributes: Dict[str, Any]) -> None:
        """Test initialization.

        Args:
            name: test name.
            attributes: test attributes from Robot Framework.
        """
        super(Test, self).__init__()
        self.name: str = name
        self.critical: str = attributes["critical"]
        self.template: str = attributes["template"]
        self.tags: List[str] = attributes["tags"]
        self.doc: str = attributes["doc"]
        self.longname: str = attributes["longname"]
        self.robot_id: str = attributes["id"]
        self.start_time: str = attributes["starttime"]
        self.status: str = attributes.get("status", "")
        self.message: Dict[str, Any] = {}
        self.end_time: str = attributes.get("endtime", "")
        self.rp_item_type: str = "STEP"
        self.type: str = "TEST"
        self.setup: Optional[Keyword] = None
        self.teardown: Optional[Keyword] = None
        self.steps: List[Keyword] = []

    def update(self, attributes: Dict[str, Any]) -> None:
        """Update test STATUS, MESSAGE and ENDTIME.

        Args:
            attributes (dict): test attributes.
        """
        self.status = attributes.get("status", "")
        self.tags = attributes.get("tags", [])
        self.end_time = attributes.get("endtime", "")


class Keyword(object):
    """Object describes keyword."""

    def __init__(self, name: str, attributes: Dict[str, Any], parent: Union[Suite, Test, "Keyword"]) -> None:
        """Keyword initialization.

        Args:
            name: keyword name with library name.
            attributes: keyword attributes from Robot Framework.
            parent: parent object, may be Keyword, Test or Suite.
        """
        super(Keyword, self).__init__()
        self.name = name
        self.libname: str = attributes["libname"]
        self.keyword_name: str = attributes["kwname"]
        self.doc: str = attributes["doc"]
        self.tags: List[str] = attributes["tags"]
        self.args: List[str] = attributes["args"]
        self.assign: List[str] = attributes["assign"]
        self.start_time: str = attributes["starttime"]
        self.end_time: str = attributes.get("endtime", "")
        self.status: str = attributes.get("status", "")
        self.parent = parent
        self.messages: List[Dict[str, Any]] = []
        self.steps: List[Keyword] = []
        self.type: str = attributes["type"]

        self._rp_item_type: Optional[str] = None

    @property
    def rp_item_type(self) -> str:
        """Get Report Portal item type.

        Returns:
            Item type.
        """
        if self._rp_item_type is None:
            if self.type == "Setup":
                self._rp_item_type = f"BEFORE_{self.parent.type}"
            elif self.type == "Teardown":
                self._rp_item_type = f"AFTER_{self.parent.type}"
            else:
                self._rp_item_type = "STEP"
        return self._rp_item_type

    @property
    def is_wuks(self) -> bool:
        """Define if current keyword is WUKS.

        Returns:
            True if this keyword is Wait Until Keyword Succeeds, else - False.
        """
        return self.name in [u"BuiltIn.Wait Until Keyword Succeeds"]

    @property
    def is_top_level(self) -> bool:
        """Check keyword at top level or not.

        Returns:
            Boolean.
        """
        if isinstance(self.parent, Keyword):
            return self.parent.rp_item_type != "STEP" and self.rp_item_type == "STEP"
        else:
            return self.rp_item_type == "STEP"

    @property
    def is_setup_or_teardown(self) -> bool:
        """Check keyword is at Setup/Teardown or not.

        Returns:
            Boolean.
        """
        return self.rp_item_type != "STEP"

    def get_name(self) -> str:
        """Get keyword name.

        Returns:
            Name is cropped up to 256 characters.
        """
        assignment = f"{', '.join(self.assign)} = " if self.assign else ""
        arguments = ", ".join(self.args)
        full_name = f"{assignment}{self.name} ({arguments})"
        return full_name[:256]

    def update(self, attributes: Dict[str, Any]) -> None:
        """Update keyword STATUS and ENDTIME.

        Args:
            attributes (dict): keyword attributes.
        """
        self.status = attributes.get("status", "")
        self.end_time = attributes.get("endtime", "")
