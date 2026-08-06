import json
import os
import sys
import copy

<<<<<<< HEAD

def _state_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


SAVE_FILE = os.path.join(_state_dir(), "save_data.json")
=======
if getattr(sys, "frozen", False):
    _save_dir = os.path.dirname(sys.executable)
else:
    _save_dir = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(_save_dir, "save_data.json")
>>>>>>> 7d92dc4dbe289288da131eadc2e39b62d6622ba5

DEFAULT_STATE = {
    "money": 1000,
    "owned_weapons": ["AK47"],
    "equipped_primary": "AK47",
    "equipped_secondary": "Glock19",
    "equipped_melee": "Knife",
    "equipped_explosive": "Grenade",
    "grenades": 3,
    "upgrades": {},
}

WEAPON_PRICES = {
    "AK47": 0,
    "Glock19": 500,
    "Knife": 300,
    "Grenade": 200,
}

WEAPON_UPGRADES = {
    "AK47": {
        "Extended Mag": {"price": 400, "desc": "+15 magazine capacity"},
        "Damage Boost": {"price": 600, "desc": "+10 damage per bullet"},
        "Rapid Fire": {"price": 500, "desc": "Faster fire rate"},
    },
    "Glock19": {
        "Extended Mag": {"price": 300, "desc": "+8 magazine capacity"},
        "Damage Boost": {"price": 400, "desc": "+8 damage per bullet"},
        "Rapid Fire": {"price": 350, "desc": "Faster fire rate"},
    },
    "Grenade": {
        "Extra Nades": {"price": 250, "desc": "+2 grenades"},
        "Blast Radius": {"price": 500, "desc": "Larger explosion radius"},
        "More Damage": {"price": 450, "desc": "+25 explosion damage"},
    },
}

_state = None


def _load():
    global _state
    if _state is not None:
        return _state
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                _state = json.load(f)
            for key in DEFAULT_STATE:
                if key not in _state:
                    _state[key] = DEFAULT_STATE[key]
        except Exception:
            _state = copy.deepcopy(DEFAULT_STATE)
    else:
        _state = copy.deepcopy(DEFAULT_STATE)
    return _state


def _save():
    global _state
    if _state is None:
        return
    with open(SAVE_FILE, "w") as f:
        json.dump(_state, f, indent=2)


def get_money():
    return _load()["money"]


def spend(amount):
    s = _load()
    if s["money"] >= amount:
        s["money"] -= amount
        _save()
        return True
    return False


def earn(amount):
    s = _load()
    s["money"] += amount
    _save()


def buy_weapon(name):
    s = _load()
    price = WEAPON_PRICES.get(name, 9999)
    if name in s["owned_weapons"]:
        return False, "Already owned"
    if s["money"] < price:
        return False, "Not enough money"
    s["money"] -= price
    s["owned_weapons"].append(name)
    _save()
    return True, f"Bought {name}!"


def buy_upgrade(weapon, upgrade):
    s = _load()
    upgrades = s.setdefault("upgrades", {})
    weapon_upgrades = upgrades.setdefault(weapon, [])
    if upgrade in weapon_upgrades:
        return False, "Already have upgrade"
    price = WEAPON_UPGRADES.get(weapon, {}).get(upgrade, {}).get("price", 9999)
    if s["money"] < price:
        return False, "Not enough money"
    s["money"] -= price
    weapon_upgrades.append(upgrade)
    _save()
    return True, f"Applied {upgrade}!"


def get_owned():
    return _load()["owned_weapons"]


def get_upgrades(weapon):
    return _load().get("upgrades", {}).get(weapon, [])


def has_weapon(name):
    return name in _load()["owned_weapons"]


def get_grenades():
    return _load().get("grenades", 3)


def use_grenade():
    s = _load()
    if s["grenades"] > 0:
        s["grenades"] -= 1
        _save()
        return True
    return False


def add_grenades(count):
    s = _load()
    s["grenades"] = s.get("grenades", 0) + count
    _save()


def reset():
    global _state
    _state = None
    _state = copy.deepcopy(DEFAULT_STATE)
    _save()
