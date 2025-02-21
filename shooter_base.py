'''
シューティングゲームのひな形コード３（しゅんさん方式）
敵の追加
GameObjectManagerに関わる処理の流れを、所々にメモしてある。
しばらくコードに触らないと仕組みが頭から抜けて、読解に時間が掛かるため。
baseコードに残っていればいいので、改良していく際は消してOK。
'''

import pyxel

class GameObject:
    def __init__(self):
        self.exists = False
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.size = 5
        self.hp = 1

    def init(self, x, y, deg, speed):
        self.x, self.y = x, y
        self.setSpeed(deg, speed)

    def setSpeed(self, deg, speed):
        self.vx = pyxel.cos(deg) * speed
        self.vy = pyxel.sin(deg) * speed

    def update(self):
        self.move()
        self.clipScreen()

    def drawSelf(self, color):
        # 継承先クラスのdrawメソッドでこのdrawSelfが呼び出される。
        # MEMO: 今は色指定だが、スプライトに変更できそう
        pyxel.rect(self.x, self.y, self.size, self.size, color)

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def isOutSide(self) -> bool:
        x = self.x
        y = self.y
        l = self.size
        if x < 0 or pyxel.width < x+l or y < 0 or pyxel.height < y+l:
            return True
        return False
    
    def clipScreen(self):
        if self.x < 0:
            self.x = 0
        if pyxel.width < self.x + self.size:
            self.x = pyxel.width - self.size
        if self.y < 0:
            self.y = 0
        if pyxel.height < self.y + self.size:
            self.y = pyxel.height - self.size

    def dead(self):
        # 継承先クラスで消滅時の画面処理が必要なら、deadメソッドをオーバーロード
        pass

    def hurt(self, val=1):
        self.hp -= val
        if self.hp <= 0:
            self.exists = False
            self.dead()

class GameObjectManager:
    def __init__(self, Obj, num):
        self.pool = []
        for i in range(num):
            self.pool.append(Obj())

    def add(self):
        for obj in self.pool:
            if obj.exists == False:
                obj.exists = True
                return obj
        return None
    
    def update(self):
        for obj in self.pool:
            if obj.exists:
                obj.update()

    def draw(self):
        for obj in self.pool:
            if obj.exists:
                obj.draw()  # GameObjectのdrawSelfではなく、継承先クラスのdrawメソッドを呼ぶ

    def vanish(self):
        for obj in self.pool:
            if obj.exists:
                obj.hurt(999)


class Shot(GameObject):
    # App init()でShot()実行不要。クラス変数mgrにGameObjectManegerのインスタンスを格納する際、
    # GameObjectManegerインスタンス生成処理の中で、Shotのインスタンスが生成されて、mgr内のpoolに格納される仕組み
    mgr = None
    #target = None   # 誘導弾のように発射後に自機追跡する場合に必要

    '''
    Playerインスタンス内にShotインスタンスを持たせたくない。しかしPlayerクラス内にShotインスタンス生成処理を含めたい。
    classmethodにすることでそれが可能。'''
    @classmethod
    def add(cls, x, y, deg, speed):
        obj = cls.mgr.add()     # poolからお休み中のShotインスタンスを探してexists=Trueに変更
        if obj != None:
            obj.init(x, y, deg, speed)  # 現状は、GameObjectのinitメソッドを呼び出している。

    @classmethod
    def drawInfo(cls):
        num_shot = sum(obj.exists==True for obj in cls.mgr.pool)
        max_shot = len(cls.mgr.pool)
        pyxel.text(10, 15, str(num_shot)+'/'+str(max_shot), 15)

    def __init__(self):
        # App init()の Shot.mgr = GameObjectManager(Shot, 数) 実施時に、pool格納作業でこの__init__が呼ばれる
        super().__init__()  # GameObject変数定義(exists, x, y, など)
        # 以下、GameObject変数のﾃﾞﾌｫﾙﾄ値変更や、Shot専用の変数追加
        self.size = 2
        '''
        Shot専用の変数追加する場合はおそらく、GameObjectのinitメソッドをオーバーライドする必要がある。
        Shotの__init__メソッド内で、GameObjectのinitメソッドを実行するを忘れないように。
        ''' 
    
    # drawメソッドは必ず必要
    def draw(self):
        self.drawSelf(7)


class Player(GameObject):
    def __init__(self):
        super().__init__()
        self.exists = True
        self.x = pyxel.width / 2
        self.y = pyxel.height * 5 / 6
        self.size = 6

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            for i in range(5):
                Shot.add(self.x+self.size/2, self.y+self.size/2, pyxel.rndf(0, 360), pyxel.rndf(3, 7))
        dx, dy = 0, 0
        if pyxel.btn(pyxel.KEY_UP):
            dy = -1
        if pyxel.btn(pyxel.KEY_DOWN):
            dy = 1
        if pyxel.btn(pyxel.KEY_LEFT):
            dx = -1
        if pyxel.btn(pyxel.KEY_RIGHT):
            dx = 1
        if(dx == 0 and dy == 0):
            return
        speed = 4
        self.setSpeed(pyxel.atan2(dy, dx), speed)
        self.move()
        self.clipScreen()

    def draw(self):
        self.drawSelf(5)


class Enemy(GameObject):
    mgr = None
    target = None

    @classmethod
    def add(cls, eid, x, y, deg, speed):    # idだとオブジェクトid確認メソッドと名前かぶりするので、eidとする
        obj = cls.mgr.add()
        if obj != None:
            obj.init(eid, x, y, deg, speed)

    def __init__(self):
        super().__init__()
        # 継承元変数の値変更
        self.size = 10

    def init(self, eid, x, y, deg, speed):
        super().init(x, y, deg, speed)
        # Enemyインスタンス変数の追加（hp, sizeは変更）
        self.timer = 0
        self.eid = eid
        dataTbl = [              
            # MEMO: dataTblはクラス変数が良いと思ったが、self.を付けない変数なら
            # 　　　イニシャライズ作業が終わったら消えるので問題なし。
            #     （ とはいえ毎回ローカル変数を作っているので無駄だからクラス変数にしようとしたが、
            #       self.update1等は引数selfが必要。この構成で仕方なし！）
            # hp, size, self_destroy_time, func
            [],
            [5, 11, 240, self.update1],
            [3, 5, 180, self.update2],
            [3, 6, 180, self.update3],
        ]
        data = dataTbl[eid]
        self.hp = data[0]
        self.size = data[1]
        self.self_destroy_time = data[2]
        self.func = data[3]

    def update(self):
        super().update()
        self.func()
        self.timer += 1
        if self.timer >= self.self_destroy_time:
            self.hurt(999)

    def draw(self):
        color = self.eid + 3
        self.drawSelf(color)

    def update1(self):
        self.y += 1
    
    def update2(self):
        self.vx = 1.5 * pyxel.sin(self.timer * 3)

    def update3(self):
        self.vx = 2.0 * pyxel.sin(self.timer * 8)
        self.vy = 2.0 * pyxel.cos(self.timer * 8) + 0.5



class App:
    def __init__(self):
        pyxel.init(160*2,120*2)
        self.init()
        pyxel.run(self.update, self.draw)

    def init(self):
        self.player = Player()
        Shot.mgr = GameObjectManager(Shot, 64)
        Enemy.mgr = GameObjectManager(Enemy, 32)

    def update(self):
        self.player.update()
        if pyxel.btnp(pyxel.KEY_DELETE):
            Shot.mgr.vanish() 

        Shot.mgr.update()
        
        if pyxel.btnp(pyxel.KEY_1):
            eid = 1
            x, y = pyxel.rndf(pyxel.width/10, pyxel.width*9/10), pyxel.rndf(pyxel.height/15, pyxel.width*3/15)
            Enemy.add(eid, x, y, 90, 1)
        if pyxel.btnp(pyxel.KEY_2):
            eid = 2
            x, y = pyxel.rndf(pyxel.width*3/10, pyxel.width*6/10), pyxel.rndf(pyxel.height/15, pyxel.width*3/15)
            Enemy.add(eid, x, y, 90, 1)
        if pyxel.btnp(pyxel.KEY_3):
            eid = 3
            x, y = pyxel.rndf(pyxel.width/6, pyxel.width*5/6), pyxel.rndf(pyxel.height/10, pyxel.width*3/10)
            Enemy.add(eid, x, y, 90, 1)
        Enemy.mgr.update()

    def draw(self):
        pyxel.cls(0)
        self.player.draw()
        Shot.mgr.draw()
        Shot.drawInfo()
        Enemy.mgr.draw()
        pyxel.text(pyxel.width/5*2, 10, "Key Space: Shot\nKey Del: Collect\nKey 1..3: enemy appearance", 10)
App()