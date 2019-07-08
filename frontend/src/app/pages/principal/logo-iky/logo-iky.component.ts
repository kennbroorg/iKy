import { Component, OnInit, OnChanges, ViewChild, ElementRef, Input, ViewEncapsulation, AfterViewInit, AfterViewChecked, OnDestroy } from '@angular/core';
import * as $ from 'jquery';

@Component({
    selector: 'ngx-logo-iky',
    templateUrl: './logo-iky.component.html',
    styleUrls: ['./logo-iky.component.scss']
})
export class LogoIkyComponent implements OnInit, AfterViewInit, OnDestroy {
    @ViewChild('canvasLogo') private canvasContainer: ElementRef;
    @ViewChild('cardLogo') private cardContainer: ElementRef;
    
    // private card: any;
    // private canvas: any;
    private connect: any;
    
    constructor() {}

    ngOnInit() {
    }
  
    ngAfterViewInit() {

        class Connect {
            text: string;
            font: string;
        
            width: number;
            height: number;
            spacing: number;
            sharpness: number;
            sharpnessMinimum: number;
            innerMaxLength: number;
            outerMaxLength: number;
            mouseClear: number;

            bounds:any;
            mouse:any;
        
            dots: Array<any>;
            oldKey: number;
            newKey: number;
        
            colorCounter: number;
            randomCount: number;
            constructor() {
          
                // user config ---
                this.text = 'iKy'
                this.font = 'Source Sans Pro' 
          
                this.spacing = 15 // multiplier for upscaling the text
                this.sharpness = 30 // scalles down when to big for screen
                this.sharpnessMinimum = 24
                this.innerMaxLength = 20 
                this.outerMaxLength = 50 
                this.mouseClear = 30
          
                // --- end config
          
                this.bounds = {
                  top: 1,
                  left: 1,
                  right: 0,
                  bottom: 0
                }
          
                this.mouse = {
                  on: false,
                  x: 0,
                  y: 0
                }
          
                console.log("CARD---3---------------------------", card);
                console.log("WIDTH--3----------------------------", Twidth);
                console.log("HEIGHT-3-----------------------------", Theight);

                this.dots = []
                this.oldKey = 0
                this.resize()
          
                // add some random particles
                let colorCounter = 0
                let randomCount = this.width * this.height / 3000 | 0
                for (let i = 0; i < randomCount; i++) {
                  this.dots.push(
                    new Dot(
                      Math.random() * this.width | 0,
                      Math.random() * this.height | 0,
                      (this.colorCounter += 2) < 360 ? this.colorCounter : this.colorCounter = 0,
                      false
                    )
                  )
                }
                this.addText()
            }

            resize() {

                // this.width = canvas.clientWidth;
                // this.height = canvas.clientHeight;
                
                this.width = Twidth;
                this.height = Theight;
                
                this.bounds.right = this.width - 1
                this.bounds.bottom = this.height - 1
            }


            update() {

                let map = (val, a1, a2, b1, b2) => b1 + (val - a1) * (b2 - b1) / (a2 - a1)
                ctx.clearRect(0, 0, this.width, this.height)
                
                this.newKey = this.oldKey + 1
                if (this.newKey > 100000) this.newKey = 0
                
                for (let i = 0, dot1; dot1 = this.dots[i]; i++) {
                  let mouseNear = this.mouse.on &&
                    Math.abs(dot1.x - this.mouse.x) < this.mouseClear &&
                    Math.abs(dot1.y - this.mouse.y) < this.mouseClear
                
                  for (let j = i + 1, dot2; dot2 = this.dots[j]; j++) {
                
                    // is this particle inside the text, than update its framekey (unless already done)
                    if (dot1.in != this.newKey &&
                      Math.abs(dot1.x - dot2.origX) <= this.spacing &&
                      Math.abs(dot1.y - dot2.origY) <= this.spacing) dot1.in = this.newKey
                
                    // should these dots be connected..?
                    let xDiff = Math.abs(dot1.x - dot2.x) 
                    let yDiff = Math.abs(dot1.y - dot2.y)
                
                    if (!mouseNear &&
                       ((!dot1.protect && !dot2.protect && xDiff < this.outerMaxLength && yDiff < this.outerMaxLength) || 
                       (xDiff < this.innerMaxLength && yDiff < this.innerMaxLength))) {
                
                      let gradient = ctx.createLinearGradient(dot1.x, dot1.y, dot2.x, dot1.y)
                      gradient.addColorStop(0, 'hsla(' + dot1.color + ',100%,50%,' + map((xDiff+yDiff)/.5,0,70,1,0.3) + ')')
                      gradient.addColorStop(1, 'hsla(' + dot2.color + ',100%,50%,' + map((xDiff+yDiff)/2,0,70,1,0.1) + ')')
                
                      ctx.beginPath()
                      ctx.moveTo(dot1.x, dot1.y)
                      ctx.lineTo(dot2.x, dot2.y)
                        // ctx.strokeStyle = gradient
                        // ctx.strokeStyle = '#53dfcf'
                      ctx.strokeStyle = '#05fcfc'
                      ctx.lineWidth = dot1.radius / 4
                      ctx.stroke()
                
                    }
                  }
                }
                
                this.oldKey = this.newKey
                
                // call all the dots update method
                for (let dot of this.dots) dot.update(this.oldKey, this.bounds)
            
                // requestAnimationFrame(connect.update.bind(this));
                // setTimeout(function() {
                    // requestAnimationFrame(connect.update.bind(this));
                    // requestAnimationFrame(connect.update());
                    // requestAnimationFrame();
                //     connect.update();
                // }, 1000 / 15);

            }

            addText() {
                let _self = this
            
                let link = document.createElement('link')
                link.rel = 'stylesheet'
                link.type = 'text/css'
                link.href = 'https://fonts.googleapis.com/css?family=' + this.font.split(' ').join('+')
                console.log("FONT", link.href)
                document.getElementsByTagName('head')[0].appendChild(link)
            
                let xhr = new XMLHttpRequest()
                xhr.open('GET', link.href)
                xhr.onload = () => _self.buildText()
                // xhr.onerror = () => (_self.font = 'arial') & _self.buildText()
                xhr.send()
            }


            buildText() {
                if (this.text.length === 0) return
                  // space the letters out, so the arn't to close
                let spacyText = this.text.split('').join(' ')
                
                  // create another canvas
                let textCanvas = document.createElement('canvas');
                textCanvas.width = this.sharpness * spacyText.length
                textCanvas.height = this.sharpness + this.sharpness / 4
                
                let textCtx = textCanvas.getContext('2d')
                  // red since later we only take the first set of pixel anyway, but other colors  wouldn't hurt either
                textCtx.fillStyle = '#f00'
                textCtx.font = 'bold ' + this.sharpness + 'px ' + this.font
                textCtx.fillText(spacyText, 0, this.sharpness)
                
                let width = textCtx.measureText(spacyText).width | 0
                  // scale down when to big
                  // * this.spacing because we scale it up later
                if (width * this.spacing > this.width && this.sharpness > this.sharpnessMinimum) {
                  --this.sharpness
                  return this.buildText()
                }
                
                // fill the dots into the real dots array
                let colorCounter = 0
                let leftOffset = Math.max(0, (this.width - width * this.spacing) / 2 | 0)
                let topOffset = Math.max(0, (this.height - (this.sharpness + this.sharpness / 4) * this.spacing) / 2 | 0)
                
                // get the all canvas pixel values(jump 4 as there are always 4 values(red,green,blue,alpha))
                // take the red and create a dot (true = there was a colored pixel)
                let data = []
                let canvasData = textCtx.getImageData(0, 0, width, this.sharpness + this.sharpness / 4).data
                for (let i = 0; i < canvasData.length; i += 4) {
                  // there is a colored pixel
                  if (canvasData[i]) {
                    let ii = i >> 2
                    // push a new dot, also scale it up and set a color
                    this.dots.push(
                      new Dot(ii % width * this.spacing + leftOffset,
                        (ii / width | 0) * this.spacing + topOffset,
                        ii % width * this.spacing * 0.3,
                        true
                      )
                    )
                  }
                
                } // end for loop
            }
        } // Class Connect


        class Dot {

          origX: number;
          origY: number;
          vx: number;
          vy: number;
          radius: number;
          internalColor: string;
          swipSwap: boolean;
          inSwip: boolean;
          protected: boolean;
          in: any;

          constructor(public x:number, public y:number, public color:any, public protect:boolean) {
            this.origX = x
            this.origY = y
            this.vx = (Math.random() - 0.5) * 2
            this.vy = (Math.random() - 0.5) * 2
            this.radius = 1
              // this.radius = (Math.random() + 0.8) * 1.5
              // this.internalColor = 'hsla(' + color + ',100%,50%,' + this.radius * 2 + ')'
            this.internalColor = '#05fcfc'
            this.swipSwap = false
            this.inSwip = true
          }
        
          update(oldKey, bounds) {
        
            ctx.beginPath()
            ctx.fillStyle = this.internalColor
            ctx.arc(this.x, this.y, this.radius, 0, 6, false)
            ctx.fill()
        
            if (this.y < bounds.top || this.y > bounds.bottom) return this.y += this.vy = -this.vy
            if (this.x < bounds.left || this.x > bounds.right) return this.x += this.vx = -this.vx
        
            this.swipSwap = !this.swipSwap
        
            if (this.protect && this.in >= oldKey) { // it is still indside the text
              this.inSwip = true
        
              if (Math.abs(this.x - this.origX) > 10 ||
                Math.abs(this.y - this.origY) > 10) {
                if (!this.swipSwap) this.vx = -this.vx
                else this.vy = -this.vy
              }
        
              if (this.swipSwap) this.x += this.vx * 0.4
              else this.y += this.vy * 0.4
        
            } else {
              // if it was inside a text but left now
              if (this.inSwip && this.protect && Math.random() < 0.995) {
                if (!this.swipSwap) this.x += this.vx = -this.vx
                else this.y += this.vy = -this.vy
              } else this.protected = false
        
              this.inSwip = false
        
              if (this.swipSwap) this.x += this.vx
              else this.y += this.vy
            }
          }

        } // Class : Dot 

        let card = this.cardContainer.nativeElement.parentNode.parentNode.parentNode;
        let Twidth = this.cardContainer.nativeElement.parentNode.parentNode.parentNode.clientWidth;
        let Theight = this.cardContainer.nativeElement.parentNode.parentNode.parentNode.clientHeight;
        console.log("CARD-------------------------------", card);
        console.log("WIDTH-------------------------------", Twidth);
        console.log("HEIGHT-------------------------------", Theight);


        let canvas = this.canvasContainer.nativeElement;
        canvas.width = Twidth;
        canvas.height = Theight;
        // let canvas = document.getElementById('connect')
        let ctx = canvas.getContext('2d')

        this.connect = new Connect;

        // connect.update();
        setTimeout(function() {
        //    requestAnimationFrame(connect.update.bind(this));
              requestAnimationFrame(this.connect.update());
        //    // requestAnimationFrame();
            //       connect.update();
        }, 1000 / 15);
        this.connect.update();
    }

    ngOnDestroy () {
    }

 }

