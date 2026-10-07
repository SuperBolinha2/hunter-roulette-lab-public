import asyncio
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol as p
import test_protocol
from player_profile import ensure, grant_gm, equip, CATALOG, AVATARS, FRAMES, ProfileError, rename, projected
from server import serve_client, read_frame

V, B, Bs = p.parse_varint_field, p.parse_bytes_field, p.parse_bytes_fields


class ProfileTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def state(self):
        s = self._state({'homeLevel': 50, 'selectedHero': 0,
                         'heroes': [{'id': 0}], 'items': [{'id': 102000, 'number': 12345}]})
        s._accounts = {}; s._next_gid = 1000001; s.pvp_port = 0
        return s

    def test_catalog_and_grant_only_explicit_account(self):
        inv = {}; gm = ensure(inv, 'local', 'Local Hunter'); other = ensure(inv, 'other', 'Other')
        grant_gm(gm); grant_gm(gm)
        self.assertEqual((len(AVATARS), len(FRAMES), len(gm['owned'])), (51, 66, 117))
        self.assertEqual(other['owned'], [1, 1001])
        self.assertIn(1019, gm['owned'])  # Native UI hides this one, ownership remains valid.

    def test_equip_type_invalid_and_unowned(self):
        inv = {}; value = ensure(inv, 'local', 'Local Hunter')
        for i in (0, 9999, 2, 1002):
            before = copy.deepcopy(value)
            with self.assertRaises(ProfileError): equip(value, i)
            self.assertEqual(value, before)
        grant_gm(value); equip(value, 505); equip(value, 1510)
        self.assertEqual((value['icon'], value['frame']), (505, 1510))

    def test_persistence_preserves_inventory_and_separates_accounts(self):
        s = self.state(); a = s.account_for('local'); initial = copy.deepcopy(s.inventory)
        s.profile_for(a); grant_gm(s.inventory['profileLab']['accounts']['local'])
        s.equip_accessory(a, 503); s.equip_accessory(a, 1509)
        restored = self.state(); restored.inventory = json.loads(s.inventory_path.read_text(encoding='utf-8'))
        restored.account_for('other'); profile = restored.profile_for(restored.account_for('LOCAL'))
        self.assertEqual((profile['icon'], profile['frame']), (503, 1509))
        for key, value in initial.items(): self.assertEqual(restored.inventory[key], value)
        self.assertEqual(restored.profile_for(restored.account_for('other'))['owned'], [1, 1001])

    def test_disk_failure_rolls_back_equip_and_first_profile(self):
        s = self.state(); a = s.account_for('local'); before = copy.deepcopy(s.inventory)
        with patch.object(s, '_save_inventory_locked', side_effect=OSError):
            with self.assertRaises(OSError): s.profile_for(a)
        self.assertEqual(s.inventory, before)
        s.profile_for(a); grant_gm(s.inventory['profileLab']['accounts']['local'])
        before = copy.deepcopy(s.inventory)
        with patch.object(s, '_save_inventory_locked', side_effect=OSError):
            with self.assertRaises(OSError): s.equip_accessory(a, 10)
        self.assertEqual(s.inventory, before)

    def test_bad_version_preserved(self):
        s = self.state(); s.inventory['profileLab'] = {'version': 2, 'accounts': {}}
        before = copy.deepcopy(s.inventory)
        with self.assertRaises(ProfileError): s.profile_for(s.account_for('local'))
        self.assertEqual(s.inventory, before)

    def test_rename_free_then_paid_cooldown_and_restart_projection(self):
        inv = {'items':[{'id':103000,'number':25}]}
        profile = ensure(inv,'nil','Local Hunter')
        reply,_ = rename(inv,'nil',b'SuperBolinha',100000,wall_now=500000)
        self.assertEqual((profile['name'],profile['renameFree'],inv['items'][0]['number']),('SuperBolinha',0,25))
        self.assertFalse(Bs(reply,1)); self.assertEqual(V(reply,2),100000)
        with self.assertRaises(ProfileError) as ctx:rename(inv,'nil',b'Bolinha',100001,wall_now=500001)
        self.assertEqual(ctx.exception.code,513)
        # Restarted lab epoch does not reset the elapsed real-world cooldown.
        self.assertEqual(projected(profile,100000,wall_now=586400)['lastRename'],13600)
        reply,_=rename(inv,'nil',b'Bolinha',100002,wall_now=586400)
        self.assertEqual(V(Bs(reply,1)[0],2),15)
        with self.assertRaises(ProfileError) as ctx:rename(inv,'nil',b'Bolinha',100003,wall_now=586401)
        self.assertEqual(ctx.exception.code,511);self.assertEqual(inv['items'][0]['number'],15)

    def test_rename_invalid_duplicate_weighted_unicode_and_insufficient(self):
        inv={};ensure(inv,'a','Alpha');ensure(inv,'b','Beta')
        for name,code in [(b'',531),(b' ',531),(b'<b>X</b>',283),(b'bad\x00',283),
                          (b' Alpha',283),(b'\xff',283),(b'x'*13,518),(b'BETA',256),
                          (('猫'*7).encode(),518)]:
            before=copy.deepcopy(inv)
            with self.assertRaises(ProfileError) as ctx:rename(inv,'a',name,100000,wall_now=500000)
            self.assertEqual(ctx.exception.code,code);self.assertEqual(inv,before)
        rename(inv,'a',('猫'*6).encode(),100000,wall_now=500000)
        inv['profileLab']['accounts']['a']['lastRename']=0
        with self.assertRaises(ProfileError) as ctx:rename(inv,'a',b'Valid',200000,wall_now=600000)
        self.assertEqual(ctx.exception.code,410)

    def test_rename_atomic_clan_display_and_save_failure(self):
        s=self.state();a=s.account_for('nil');s.profile_for(a)
        s.inventory['clanLab']={'version':1,'teams':{'1':{'members':[{'key':'nil','display':'Local Hunter'}]}}}
        before=copy.deepcopy(s.inventory)
        with patch.object(s,'_save_inventory_locked',side_effect=OSError):
            with self.assertRaises(OSError):s.rename_player(a,b'SuperBolinha')
        self.assertEqual(s.inventory,before)
        s.rename_player(a,b'SuperBolinha')
        self.assertEqual(s.inventory['clanLab']['teams']['1']['members'][0]['display'],'SuperBolinha')
        restored=json.loads(s.inventory_path.read_text(encoding='utf-8'))
        self.assertEqual(restored['profileLab']['accounts']['nil']['renameFree'],0)
        self.assertEqual(a.name,'nil')

    def test_native_tcp_login_detail_equip_notify_relogin(self):
        async def run():
            s = self.state(); placeholder = s.account_for('local'); s.profile_for(placeholder)
            a = s.account_for('nil'); s.profile_for(a)
            actual = s.inventory['profileLab']['accounts']['nil']
            grant_gm(actual); actual['name'] = 'Local Hunter'
            self.assertEqual(s.profile_for(placeholder)['owned'], [1,1001])
            listener = await asyncio.start_server(lambda r,w: serve_client(r,w,s,'body','logic'), '127.0.0.1', 0)
            r,w = await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            def send(act, body):w.write(p.encode_frame(2,act,body,index=800+act,length_mode='body'))
            async def recv(cmd,act):
                for _ in range(8):
                    h,b,_ = await asyncio.wait_for(read_frame(r,'body'),3)
                    if (h.cmd,h.act)==(cmd,act):return h,b
                raise AssertionError((cmd,act))
            try:
                send(3,p.pb_varint(1,a.gid)); h,b = await recv(2,3)
                self.assertEqual(h.error,0); self.assertEqual(len(Bs(b,24)),117)
                self.assertTrue(all(V(v,4)==0 for v in Bs(b,24)))
                send(5,p.pb_message(p.pb_varint(1,a.gid),p.pb_varint(2,1510)))
                h,b = await recv(2,5); self.assertEqual(h.error,0)
                _,n = await recv(253,29); self.assertEqual(V(n,3),1510)
                send(9,p.pb_message(p.pb_varint(1,a.gid),p.pb_varint(2,a.gid)))
                h,b = await recv(2,9);self.assertEqual(h.error,0)
                detail = B(b,2);self.assertEqual(V(detail,6),1510)
                self.assertEqual(B(detail,4),b'Local Hunter')
                self.assertEqual(B(detail,25),p.pb_message(*(p.pb_varint(3,i) for i in AVATARS),
                                                          *(p.pb_varint(4,i) for i in FRAMES)))
                send(5,p.pb_message(p.pb_varint(1,a.gid),p.pb_varint(2,9999)))
                h,_=await recv(2,5);self.assertNotEqual(h.error,0)
                send(9,p.pb_varint(2,9999));h,_=await recv(2,9);self.assertEqual(h.error,544)
                send(2,p.pb_message(p.pb_varint(1,a.gid),p.pb_bytes(2,'SuperBolinha')))
                h,b=await recv(2,2);self.assertEqual(h.error,0);self.assertFalse(Bs(b,1))
                _,notify=await recv(253,28);self.assertEqual(V(B(notify,1),1),0)
                send(9,p.pb_message(p.pb_varint(1,a.gid),p.pb_varint(2,a.gid)))
                h,b=await recv(2,9);self.assertEqual(B(B(b,2),4),b'SuperBolinha')
                send(3,p.pb_varint(1,a.gid));h,b=await recv(2,3)
                self.assertEqual(V(B(b,22),1),0)
                self.assertGreater(V(B(b,2),13),0)
            finally:
                w.close(); await w.wait_closed(); listener.close(); await listener.wait_closed()
        asyncio.run(run())
