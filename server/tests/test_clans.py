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
from clans import request, snapshot, ClanError, CREATE_COST, EDIT_COST
from server import serve_client, read_frame

V, B, Bs = p.parse_varint_field, p.parse_bytes_field, p.parse_bytes_fields


def create_body(name='Clan de Teste', icon=1, desc='Teste local'):
    return p.pb_message(p.pb_varint(1,1000001),p.pb_varint(2,icon),p.pb_bytes(3,name),p.pb_bytes(4,desc))


class ClanTests(unittest.TestCase):
    _state=test_protocol.ProtocolTests._state

    def state(self, balance=800000, level=50):
        state=self._state({'homeLevel':level,'items':[{'id':102000,'number':balance}],
                           'selectedHero':0,'heroes':[{'id':0,'skillId':10000,'starLevel':5}]})
        state._accounts={};state._next_gid=1000001;state.pvp_port=0
        return state

    def test_create_cost_native_profile_and_leader(self):
        s=self.state();a=s.account_for('local')
        reply, notices=s.handle_clan(a,4,create_body())
        team=B(reply,1);member=Bs(team,3)[0]
        self.assertEqual((V(team,1),B(team,4).decode(),V(member,1),V(member,2)),(10001,'Clan de Teste',a.gid,1))
        self.assertEqual(s.currency(102000),300000)
        self.assertEqual(V(Bs(reply,2)[0],2),300000)
        self.assertEqual([act for act,_ in notices],[74,70])
        ct,gt=s.clan_login(a)
        self.assertEqual(B(ct,4),B(gt,4));self.assertEqual(V(gt,1),10001)
        self.assertEqual(s.inventory['heroes'][0]['starLevel'],5)

    def test_persistence_restart_with_reversed_account_id_order(self):
        s=self.state();a=s.account_for('Local');s.handle_clan(a,4,create_body())
        restored=self.state();restored.inventory=json.loads(s.inventory_path.read_text(encoding='utf-8'))
        other=restored.account_for('Other');owner=restored.account_for('Local')
        ct,gt=restored.clan_login(owner)
        self.assertEqual((V(Bs(ct,3)[0],1),V(gt,1)),(owner.gid,10001))
        self.assertNotEqual(owner.gid,a.gid)
        self.assertIsNone(restored.clan_login(other)[0])
        self.assertEqual(restored.currency(102000),300000)

    def test_duplicate_membership_name_and_insufficient_funds_no_charge(self):
        s=self.state();a=s.account_for('local');s.handle_clan(a,4,create_body())
        for caller,name,expected in ((a,'Outro Nome',789),(s.account_for('other'),'CLAN DE TESTE',750)):
            before=copy.deepcopy(s.inventory)
            with self.assertRaises(ClanError) as ctx:s.handle_clan(caller,4,create_body(name))
            self.assertEqual(ctx.exception.code,expected);self.assertEqual(s.inventory,before)
        poor=self.state(balance=CREATE_COST-1);a=poor.account_for('local')
        with self.assertRaises(ClanError) as ctx:poor.handle_clan(a,4,create_body())
        self.assertEqual(ctx.exception.code,423);self.assertNotIn('clanLab',poor.inventory)

    def test_level_names_lengths_utf8_and_locked_icon(self):
        low=self.state(level=6);a=low.account_for('local')
        with self.assertRaises(ClanError) as ctx:low.handle_clan(a,4,create_body())
        self.assertEqual(ctx.exception.code,784)
        for body in (create_body(''),create_body('x'*17),create_body('<b>Clã</b>'),
                     create_body(desc='x'*31),create_body(icon=6),
                     p.pb_message(p.pb_varint(2,1),p.pb_bytes(3,b'\xff'))):
            s=self.state();a=s.account_for('local');before=copy.deepcopy(s.inventory)
            with self.assertRaises(ClanError):s.handle_clan(a,4,body)
            self.assertEqual(s.inventory,before)
        for name in ('Clã Águia','Охотники','Les chasseurs'):
            s=self.state();s.handle_clan(s.account_for('local'),4,create_body(name))
            self.assertEqual(s.inventory['clanLab']['teams']['10001']['name'],name)

    def test_list_search_detail_members_and_random_name(self):
        s=self.state();a=s.account_for('local');s.handle_clan(a,4,create_body())
        outsider=s.account_for('visitor')
        body,notes=s.handle_clan(outsider,1,p.pb_varint(1,outsider.gid))
        self.assertEqual(B(Bs(body,2)[0],7).decode(),'Clan de Teste')
        for act in (2,5,6,8):
            body,notes=s.handle_clan(outsider,act,p.pb_varint(2,10001))
            self.assertTrue(body)
        self.assertEqual(s.handle_clan(a,7,b'')[0],p.pb_bytes(1,'Local Hunters'))
        with self.assertRaises(ClanError) as ctx:s.handle_clan(a,6,p.pb_varint(2,999999))
        self.assertEqual(ctx.exception.code,369)

    def test_edit_cost_cooldown_and_non_owner_permissions(self):
        s=self.state(balance=1000000);a=s.account_for('local');s.handle_clan(a,4,create_body())
        before=copy.deepcopy(s.inventory);other=s.account_for('other')
        with self.assertRaises(ClanError):s.handle_clan(other,15,create_body('Renamed'))
        self.assertEqual(s.inventory,before)
        s.handle_clan(a,15,create_body('Renamed'))
        self.assertEqual(s.currency(102000),1000000-CREATE_COST-EDIT_COST)
        before=copy.deepcopy(s.inventory)
        with self.assertRaises(ClanError) as ctx:s.handle_clan(a,15,create_body('Again'))
        self.assertEqual(ctx.exception.code,785);self.assertEqual(s.inventory,before)
        s.handle_clan(a,14,p.pb_bytes(2,p.pb_varint(1,1)))
        self.assertTrue(s.inventory['clanLab']['teams']['10001']['quickJoin'])

    def test_member_not_leader_cannot_edit_even_with_forged_body_gid(self):
        s=self.state();a=s.account_for('local');s.handle_clan(a,4,create_body())
        other=s.account_for('other')
        s.inventory['clanLab']['teams']['10001']['members'].append(
            dict(key='other',account='other',display='Other',level=50,icon=1,joined=0))
        with self.assertRaises(ClanError) as ctx:s.handle_clan(other,15,create_body('Forgery'))
        self.assertEqual(ctx.exception.code,759)

    def test_persistence_failure_rolls_back_currency_and_clan(self):
        s=self.state();a=s.account_for('local');before=copy.deepcopy(s.inventory)
        with patch.object(s,'_save_inventory_locked',side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):s.handle_clan(a,4,create_body())
        self.assertEqual(s.inventory,before)
        s.handle_clan(a,4,create_body())
        self.assertEqual(s.inventory['clanLab']['nextId'],10002)

    def test_incompatible_store_not_silently_erased(self):
        s=self.state();a=s.account_for('local');s.inventory['clanLab']={'version':999,'teams':{}}
        before=copy.deepcopy(s.inventory)
        with self.assertRaises(ClanError) as ctx:s.clan_login(a)
        self.assertEqual(ctx.exception.code,754);self.assertEqual(s.inventory,before)

    def test_no_reward_or_unsupported_membership_success(self):
        s=self.state();a=s.account_for('local');s.handle_clan(a,4,create_body())
        for act,code in ((17,772),(3,757),(9,757),(10,757),(11,757),(12,757),(13,757),(16,757)):
            before=copy.deepcopy(s.inventory)
            with self.assertRaises(ClanError) as ctx:s.handle_clan(a,act,p.pb_varint(2,10001))
            self.assertEqual(ctx.exception.code,code);self.assertEqual(s.inventory,before)

    def test_tcp_create_notifies_login_restores_and_read_detail(self):
        async def run():
            s=self.state();listener=await asyncio.start_server(lambda r,w:serve_client(r,w,s,'body','logic'),'127.0.0.1',0)
            r,w=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_=await read_frame(r,'body')
                        if (h.cmd,h.act,h.index)==(cmd,act,index):return h,b
            def send(cmd,act,body,index):w.write(p.encode_frame(cmd,act,body,index=index,length_mode='body'))
            try:
                send(47,4,create_body(),901)
                h,b=await receive(47,4,901);self.assertEqual(h.error,0)
                self.assertEqual(B(B(b,1),4).decode(),'Clan de Teste')
                _,profile=await receive(253,74);self.assertEqual(V(B(profile,1),1),10001)
                await receive(253,70)
                send(2,3,p.pb_varint(1,1000001),902)
                h,b=await receive(2,3,902);self.assertEqual(h.error,0)
                self.assertEqual(B(B(b,32),4),B(B(b,33),4))
                self.assertEqual(V(B(b,33),1),10001)
                send(47,6,p.pb_varint(1,1000001)+p.pb_varint(2,10001),903)
                h,b=await receive(47,6,903);self.assertEqual(h.error,0)
                self.assertEqual(B(B(b,1),4).decode(),'Clan de Teste')
                send(47,4,create_body('Another'),904)
                h,_=await receive(47,4,904);self.assertEqual(h.error,789)
                self.assertEqual(s.currency(102000),300000)
            finally:
                w.close();await w.wait_closed();listener.close();await listener.wait_closed()
        asyncio.run(run())
