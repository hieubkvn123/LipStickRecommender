import React, { Component } from 'react'
import ReactDOM from 'react-dom'
import { InputGroup, FormControl, Button } from 'react-bootstrap'
import { Modal } from 'react-bootstrap'
import ImageGallery from 'react-image-gallery'
import axios from 'axios'

// CSS
import './css/main.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import "react-image-gallery/styles/css/image-gallery.css";

class HomePage extends Component {
	constructor(props){
		super(props)
		this.state = {
			'selfie_file' : '/logo192.png', 
			'display_info' : false, 
			'display_gallery' : false,
			'R' : 0,
			'G' : 0,
			'B' : 0,
			'color_hex' : '#000000',
			'lip_type' : 'matte',
			'lipstick_images' : []
		}
	
		// binding event handlers
		this.fileChange = this.fileChange.bind(this)
		this.handleGalleryClose = this.handleGalleryClose.bind(this)
		this.handleGalleryOpen = this.handleGalleryOpen.bind(this)
	}

	componentDidMount(){

	}

	componentWillUnmount() {

	}

	handleGalleryClose() {
		this.setState({display_gallery : false})
	}

	handleGalleryOpen() {
		this.setState({display_gallery : true})
	}

	fileChange(e){
		this.setState({display_load_screen : true})
		this.setState({display_info : false})
		this.setState({
			'selfie_file' : URL.createObjectURL(e.target.files[0])
		})

		// send this file to server for processing
		var formData = new FormData()
		formData.append('img', e.target.files[0])
		axios({
			method : 'post',
			data : formData,
			url : 'http://localhost:8080/upload',
			headers : {
				'Content-Type' : 'multipart/form-data'
			}
		}).then(response => { // on success
			if(response.data === 'no_face_detected'){
				alert('Please upload a picture with your face clear and exposed')
			}else if(response.data === 'more_than_one_face_detected'){
				alert('Please upload a picture with one face only')
			}else{
				this.setState({display_info : true})
				this.setState({display_load_screen : false})

				var data = response.data
				this.setState({R : data['lip_color']['R']})
				this.setState({G : data['lip_color']['G']})
				this.setState({B : data['lip_color']['B']})
				this.setState({'color_hex' : data['lip_color']['HEX']})
				this.setState({'lip_type' : data['lip_type']})

				var images = []
				data['recommendation'].forEach((value, index) => {
					var item = {
						original : value['url'],
						thumbnail : value['url']
					}

					console.log(value)

					images.push(item)
				})

				this.setState({lipstick_images : images})
			}
		}).catch(error => {
			console.log(error)
			alert('Cannot communicate with API')
		})
	}

	triggerInputFile = () => this.fileInput.click()

	render() {
		return (
			<div id='container'>
				<div id="image-region">
					<img id='image' src={this.state.selfie_file}/>
				</div>

				{/* The Gallery dialog */}
				<Modal show={this.state.display_gallery} onHide={this.handleGalleryClose} backdrop="static" keyboard={true}>
			        <Modal.Header closeButton>
			        	<Modal.Title>Brand Recommendation</Modal.Title>
			        </Modal.Header>
			        <Modal.Body>
			          <ImageGallery items={this.state.lipstick_images} />
			        </Modal.Body>
			        <Modal.Footer>
			          	<Button variant="secondary" onClick={this.handleGalleryClose}>
			            Close
			          	</Button>
			        </Modal.Footer>
			    </Modal>

				<div id="utils">	
					<h2>Upload your selfie</h2>
					<input type='file' id='selfie-upload' ref={fileInput => this.fileInput = fileInput} onChange={this.fileChange} className='form-control'/>
					
					<InputGroup className="mb-3">
					    <InputGroup.Prepend>
					      <Button id='upload-button' onClick={this.triggerInputFile} variant="primary">Upload File</Button>
					    </InputGroup.Prepend>
					    <FormControl
					      placeholder={this.state.selfie_file}
					      aria-label="Selfie image"
					      aria-describedby="basic-addon1"
					    />
					  </InputGroup>
					  <div id='color-info-panel' hidden={!this.state.display_info}>
							<h2>Lip color</h2>
							<div style={{'display' : 'block', 'width': '100%', 'height':'200px'}}>
								<div id='lip-color' style={{background:`rgb(${this.state.R}, ${this.state.G}, ${this.state.B})`}}></div>
								<p id='color-info-text'>
									<table>
										<tr>
											<td>
												<span className='header'>Lip Color in rgb :</span>
											</td>
											<td style={{'float':'right'}}>
												rgb({this.state.R}, {this.state.G}, {this.state.B})
											</td>
										</tr>
										<tr>
											<td>
												<span className='header'>Lip Color in hex :</span>
											</td>
											<td style={{'float':'right'}}>
												{this.state.color_hex} 
											</td>
										</tr>

										<tr>
											<td>
												<span className='header'>Lip Type :</span>
											</td>
											<td style={{'float':'right'}}>
												{this.state.lip_type} 
											</td>
										</tr>
									</table>
								</p>
							</div>

							<h2 style={{'display' : 'block'}}>Recommended Color (Dior)</h2>
							<button id='recommend-button' onClick={this.handleGalleryOpen} className='btn btn-info' type='button'>See recommendation from database</button>

							</div>
							<div id='loading-screen' hidden={!this.state.display_load_screen}>
								<img src='/loading.gif'/>
							</div>
				</div>
			</div>
		)
	}
}

export default HomePage